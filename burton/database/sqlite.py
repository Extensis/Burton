import codecs
import os
import sqlite3

from pkg_resources import resource_stream

import burton
from burton import parser

class SQLite(object):
    """The SQLite class facilitates saving localization data to a SQLite
    database for the purpose of comparing the localization state between
    platforms.

    All database operations support duck typing, so it is possible to implement
    implement database classes for other database backends. The database class
    used can be set in the config file. Methods beginning with an understore are
    not part of the duck typing and do not have to be implemented in other
    classes.

    This class does not save the SQLite database, but instead dumps its contents
    to a SQL file that it checks in to VCS. On subsequent runs, of that SQL file
    is present, the class will load that file into a new database. Otherwise it
    will create a new database with the correct schema.

    In the config file, database_path should be set to this SQL file, not to a
    SQLite database file.
    """

    def __init__(self, filename):
        object.__init__(self)
        self.filename = filename
        self.dbh      = None
        self._temp_filename = filename + ".db"

    def update_from_vcs(self, vcs, submodule_path = None):
        """Gets the latest version of the SQL file from VCS and opens it for
        editing. If using VCS, call this method before calling connect.
        """

        full_path = os.path.abspath(self.filename)
        vcs.add_file(full_path, submodule_path)

    def connect(self):
        """Opens the database connection, loading the SQL file if present, or a
        schema file if not.
        """
        should_load_schema = False
        if not os.path.exists(self.filename):
            should_load_schema = True

        self._connect()

        if should_load_schema:
            self._load_schema()
        else:
            self._load_database()

    def _connect(self):
        if os.path.exists(self._temp_filename):
            self._remove_temporary_file()
        self.dbh = sqlite3.connect(self._temp_filename)

    def _schema_file(self):
        return resource_stream(__name__, "sqlite.schema")
        
    def _load_schema(self):
        cursor = self.dbh.cursor()
        fp = self._schema_file()
        contents = fp.read()
        if isinstance(contents, bytes):
            contents = contents.decode()
        cursor.executescript(
          contents
        )
        fp.close()

        self.dbh.commit()

    def _load_database(self):
        cursor = self.dbh.cursor()
        fp = self._open_for_reading(self.filename)
        cursor.executescript(fp.read())
        fp.close()
        cursor.close()
        self.dbh.commit()

    def disconnect(self):
        """Saves the contents of the database to a SQL file, closes the database
        connection, and removes the SQLite database file.
        """
        self._save_database()
        self.dbh.close()
        self._remove_temporary_file()

    def _save_database(self):
        output_file = self._open_for_writing(self.filename)
        for line in self.dbh.iterdump():
            output_file.write("%s\n" % line)

        output_file.close()

    def _remove_temporary_file(self):
        os.remove(self._temp_filename)

    def write_string_mapping_for_platform(self, platform, mapping):
        """This method takes in a dictionary of native-language string mappings,
        which can be acquired from StringMapping's string_mapping_dict property,
        and a string representing the platform, which can be acquired from the
        ConfigFile. It writes the mapping to the database for the platform,
        translating any platform-specific string paramaters (e.g. %s, {0}) to a
        platform-neutural, localizable format.

        If the platform does not exist in the database, this method will add it
        before writing the mapping to the database.

        If there is an existing mapping for the platform in the database, this
        method will merge the new mapping with the mapping in the database, and
        will delete native-language translations that are not present in the new
        mapping. It will also update the last_updated column on translation_keys
        for any native-language translation it updates or deletes.
        """

        platform_no  = self._get_platform_no(platform)

        self._insert_new_translation_keys(platform_no, mapping)
        self._insert_update_or_delete_native_translations(platform_no, mapping)
        self.dbh.commit()

    def get_all_translation_keys(self):
        cursor = self.dbh.cursor()
        cursor.execute(
            """select
                translation_key
            from translation_keys
            """,
        )

        results = [key[0].decode("unicode_escape") for key in cursor.fetchall()]
        return results

    def get_all_native_translations(self):
        cursor = self.dbh.cursor()
        cursor.execute(
            """select distinct
                translation
            from native_translations
            """,
        )

        results = [key[0].decode("unicode_escape") for key in cursor.fetchall()]
        return results

    def _insert_new_translation_keys(self, platform_no, mapping):
        remaining_mappings = mapping.copy()
        cursor = self.dbh.cursor()

        translation_keys = self.get_all_translation_keys()

        for translation_key in translation_keys:
            if translation_key in remaining_mappings:
                del remaining_mappings[translation_key]

        for mapping_key in remaining_mappings:
            cursor.execute(
                """insert into translation_keys (
                    translation_key,
                    last_updated
                ) values (
                    ?,
                    {0}
                )
                """.format(self._get_current_time()),
                (mapping_key.encode("unicode_escape"),)
            )

        cursor.close()

    def _insert_update_or_delete_native_translations(
        self,
        platform_no,
        mapping
    ):
        cursor = self.dbh.cursor()
        cursor.execute(
            """select
                translation_key_no,
                translation_key,
                translation
            from translation_keys
            inner join native_translations
                using (translation_key_no)
            where platform_no = ?
            """,
            (platform_no,)
        )
        results = cursor.fetchall()
        translations_in_db = { }

        for translation_key_no, translation_key, translation in results:
            translation_key = translation_key.decode("unicode_escape")
            translation = translation.decode("unicode_escape")
            translations_in_db[translation_key] = \
                (translation_key_no, translation)

        self._delete_defunct_native_translations(
            platform_no,
            mapping,
            translations_in_db
        )
        self._insert_or_update_native_translations(
            platform_no,
            mapping,
            translations_in_db
        )

    def _delete_defunct_native_translations(
        self,
        platform_no,
        mapping,
        translations_in_db
    ):
        translation_keys_to_update = set([])

        cursor = self.dbh.cursor()
        for translation_key in translations_in_db:
            if translation_key not in mapping:
                translation_key_no = translations_in_db[translation_key][0]
                cursor.execute(
                    """delete from native_translations
                    where translation_key_no = ?
                        and platform_no = ?
                    """,
                    (
                        translation_key_no,
                        platform_no,
                    )
                )
                translation_keys_to_update.add(translation_key_no)

        cursor.close()
        self._update_timestamp_on_translation_keys(translation_keys_to_update)

    def _insert_or_update_native_translations(
        self,
        platform_no,
        mapping,
        translations_in_db
    ):
        translation_keys_to_update = set([])

        for translation_key in mapping:
            if translation_key in translations_in_db:
                translation_key_no, translation = \
                    translations_in_db[translation_key]

                if mapping[translation_key] != translation:
                    self._update_native_translation(
                        translation_key_no,
                        platform_no,
                        mapping[translation_key]
                    )

                    translation_keys_to_update.add(translation_key_no)

            else:
                translation_keys_to_update.add(
                    self._insert_native_translation(
                        platform_no,
                        translation_key,
                        mapping[translation_key]
                    )
                )

        self._update_timestamp_on_translation_keys(translation_keys_to_update)

    def _insert_native_translation(
        self,
        platform_no,
        translation_key,
        translation
    ):
        filtered_translation, replaced_params = \
            parser.replace_params(translation)

        cursor = self.dbh.cursor()
        translation_key_no = cursor.execute(
            """select translation_key_no
            from translation_keys
            where translation_key = ?
            """,
            (
                translation_key.encode("unicode_escape"),
            )
        ).fetchone()[0]

        cursor.execute(
            """insert into native_translations (
                translation_key_no,
                platform_no,
                translation
            ) values (
                ?,
                ?,
                ?
            )
            """,
            (
                translation_key_no,
                platform_no,
                translation.encode("unicode_escape"),
            )
        )

        native_translation_no = self._get_native_translation_no(
            translation_key_no,
            platform_no
        )

        self._update_replaced_params(
            platform_no,
            native_translation_no,
            replaced_params
        )

        cursor.close()
        return translation_key_no

    def _update_native_translation(
        self,
        translation_key_no,
        platform_no,
        translation
    ):
        filtered_translation, replaced_params = \
            parser.replace_params(translation)

        native_translation_no = self._get_native_translation_no(
            translation_key_no,
            platform_no
        )

        cursor = self.dbh.cursor()
        cursor.execute(
            """update native_translations
                set translation = ?
            where native_translation_no = ?
            """,
            (
                translation.encode("unicode_escape"),
                native_translation_no,
            )
        )

        cursor.execute(
            """delete from replaced_params
            where platform_no = ?
                and native_translation_no = ?
            """,
            (
                platform_no,
                native_translation_no,
            ),
        )

        self._update_replaced_params(
            platform_no,
            native_translation_no,
            replaced_params
        )

        cursor.close()

    def _update_replaced_params(
        self,
        platform_no,
        native_translation_no,
        replaced_params
    ):
        cursor = self.dbh.cursor()
        replaced_param_index = 0
        for replaced_param in replaced_params:
            cursor.execute(
                """insert into replaced_params (
                    platform_no,
                    native_translation_no,
                    param_index,
                    param_string
                ) values (
                    ?,
                    ?,
                    ?,
                    ?
                );
                """,
                (
                    platform_no,
                    native_translation_no,
                    replaced_param_index,
                    replaced_param.encode("unicode_escape"),
                )
            )

            replaced_param_index += 1

    def _update_timestamp_on_translation_keys(self, translation_keys_to_update):
        cursor = self.dbh.cursor()
        for translation_key_no in translation_keys_to_update:
            cursor.execute(
                """update translation_keys
                    set last_updated = {0}
                where translation_key_no = ?
                """.format(self._get_current_time()),
                (
                    translation_key_no,
                )
            )

    def _get_platform_no(self, platform):
        cursor = self.dbh.cursor()
        cursor.execute(
            "select platform_no from platforms where name = ?",
            (platform,)
        )
        results = cursor.fetchall()
        cursor.close()

        platform_no = None
        if len(results) > 0:
            platform_no = results[0][0]
        else:
            cursor = self.dbh.cursor()
            cursor.execute(
                "insert into platforms (name) values (?)",
                (platform,)
            )
            self.dbh.commit()
            cursor.close()
            return self._get_platform_no(platform)

        return platform_no

    def _get_native_translation_no(self, translation_key_no, platform_no):
        cursor = self.dbh.cursor()
        native_translation_no = cursor.execute(
            """select native_translation_no
            from native_translations
            where translation_key_no = ?
                and platform_no = ?
            """,
            (
                translation_key_no,
                platform_no,
            )
        ).fetchone()[0]

        cursor.close()
        return native_translation_no

    def remove_old_unmapped_strings(self):
        cursor = self.dbh.cursor()
        cursor.execute(
            """delete from translation_keys
            where translation_key_no not in (
                select translation_key_no
                from native_translations
            )
                and last_updated < {0}
            """.format(self._get_translation_key_date_threshold())
        )

    def get_platforms(self):
        cursor = self.dbh.cursor()
        cursor.execute("select name from platforms")

        return_value = [result[0] for result in cursor.fetchall()]
        cursor.close()

        return return_value

    def get_string_mapping_for_platform(self, platform):
        platform_no = self._get_platform_no(platform)

        cursor = self.dbh.cursor()
        cursor.execute("""
            select
                translation_key,
                translation
            from translation_keys
            inner join native_translations
                using (translation_key_no)
            where platform_no = ?
        """,
            ( platform_no, )
        )

        results = dict(cursor.fetchall())
        cursor.close()

        return_value = { }
        print(results)
        for translation_key in results:
            return_value[translation_key.decode("unicode_escape")] = \
                results[translation_key].decode("unicode_escape")

        return return_value

    def get_native_translations_for_platform(self, platform):
        return_value = { }
        platform_no = self._get_platform_no(platform)

        cursor = self.dbh.cursor()
        cursor.execute("""
            select translation
            from native_translations
            where platform_no = ?
        """,
            ( platform_no, )
        )

        results = [key[0].decode("unicode_escape") for key in cursor.fetchall()]

        cursor.close()

        return results

    def _get_current_time(self):
        return "datetime('now')"

    def _get_translation_key_date_threshold(self):
        return "datetime('now', '-90 days')"

    def _open_for_reading(self, filename):
        return open(filename, "r")

    def _open_for_writing(self, filename):
        return codecs.open(filename, "w", "utf-8")
