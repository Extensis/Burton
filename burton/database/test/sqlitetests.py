import codecs
import mock
import os
import sqlite3
import unittest

from io import StringIO

from burton import database

class SQLiteTests(unittest.TestCase):
    def tearDown(self):
        if os.path.exists('some_filename.db'):
            os.remove('some_filename.db')

    def test_write_string_mapping_for_platform(self):
        db = database.SQLite("some_filename")

        def _connect(*args, **kwargs):
            db.dbh = sqlite3.connect(":memory:")

        def _disconnect(*args, **kwargs):
            db.dbh.close()

        db._connect = mock.Mock(side_effect = _connect)
        db.disconnect = mock.Mock(side_effect = _disconnect)
        db._get_current_time = mock.Mock(
            return_value = "datetime('2010-12-02 02:20:00')"
        )

        db.connect()
        db.write_string_mapping_for_platform(
            "Mac",
            {
                "SomeString" : "Translation for some string",
                "OtherString" : "Translation for some other string",
            }
        )

        cursor = db.dbh.cursor()
        self.assertEquals(
            cursor.execute("select * from translation_keys").fetchall(),
            [
                (1, b"SomeString", "2010-12-02 02:20:00"),
                (2, b"OtherString", "2010-12-02 02:20:00")
            ],
        )

        self.assertEquals(
            cursor.execute("select * from native_translations").fetchall(),
            [
                (1, 1, 1, b"Translation for some string"),
                (2, 2, 1, b"Translation for some other string")
            ],
        )

        db._get_current_time = mock.Mock(
            return_value = "datetime('2010-12-02 02:21:00')"
        )

        db.write_string_mapping_for_platform(
            "Win",
            {
                "SomeString" : "Translation for some string",
                "OtherString" : "Translation for some other string",
            }
        )

        self.assertEquals(
            cursor.execute("select * from translation_keys").fetchall(),
            [
                (1, b"SomeString", "2010-12-02 02:21:00"),
                (2, b"OtherString", "2010-12-02 02:21:00")
            ],
        )

        self.assertEquals(
            cursor.execute("select * from native_translations").fetchall(),
            [
                (1, 1, 1, b"Translation for some string"),
                (2, 2, 1, b"Translation for some other string"),
                (3, 1, 2, b"Translation for some string"),
                (4, 2, 2, b"Translation for some other string")
            ],
        )

        db._get_current_time = mock.Mock(
            return_value = "datetime('2010-12-02 02:22:00')"
        )
        db.write_string_mapping_for_platform(
            "Mac",
            {
                "SomeString" : "New translation for some string",
                "OtherString" : "Translation for some other string",
            }
        )

        self.assertEquals(
            cursor.execute("select * from translation_keys").fetchall(),
            [
                (1, b"SomeString", "2010-12-02 02:22:00"),
                (2, b"OtherString", "2010-12-02 02:21:00")
            ],
        )

        self.assertEquals(
            cursor.execute("select * from native_translations").fetchall(),
            [
                (1, 1, 1, b"New translation for some string"),
                (2, 2, 1, b"Translation for some other string"),
                (3, 1, 2, b"Translation for some string"),
                (4, 2, 2, b"Translation for some other string")
            ],
        )

        db._get_current_time = mock.Mock(
            return_value = "datetime('2010-12-02 02:23:00')"
        )
        db.write_string_mapping_for_platform(
            "Win",
            {
                "SomeString" : "New translation for some string",
            }
        )

        self.assertEquals(
            cursor.execute("select * from translation_keys").fetchall(),
            [
                (1, b"SomeString", "2010-12-02 02:23:00"),
                (2, b"OtherString", "2010-12-02 02:23:00")
            ],
        )

        self.assertEquals(
            cursor.execute("select * from native_translations").fetchall(),
            [
                (1, 1, 1, b"New translation for some string"),
                (2, 2, 1, b"Translation for some other string"),
                (3, 1, 2, b"New translation for some string")
            ],
        )

        db.disconnect()

    def test_write_string_mapping_for_platform_translates_params(self):
        db = database.SQLite("some_filename")

        def _connect(*args, **kwargs):
            db.dbh = sqlite3.connect(":memory:")

        def _disconnect(*args, **kwargs):
            db.dbh.close()

        db._connect = mock.Mock(side_effect = _connect)
        db.disconnect = mock.Mock(side_effect = _disconnect)
        db._get_current_time = mock.Mock(
            return_value = "datetime('2010-12-02 02:20:00')"
        )

        db.connect()
        db.write_string_mapping_for_platform(
            "Mac",
            {
                "SomeString" : "%03d of %03.3lld for {0} %@",
            }
        )

        cursor = db.dbh.cursor()
        self.assertEquals(
            cursor.execute("select * from translation_keys").fetchall(),
            [
                (1, b"SomeString", "2010-12-02 02:20:00"),
            ],
        )

        self.assertEquals(
            cursor.execute("select * from native_translations").fetchall(),
            [
                (1, 1, 1, b"%03d of %03.3lld for {0} %@"),
            ],
        )

        self.assertEquals(
            cursor.execute("select * from replaced_params").fetchall(),
            [
                (1, 1, 1, 0, b"%03d" ),
                (2, 1, 1, 1, b"%03.3lld"),
                (3, 1, 1, 2, b"{0}"     ),
                (4, 1, 1, 3, b"%@"      ),
            ],
        )

        db.write_string_mapping_for_platform(
            "Mac",
            {
                "SomeString" : "%03d of %03.3lld",
            }
        )

        self.assertEquals(
            cursor.execute("select * from native_translations").fetchall(),
            [
                (1, 1, 1, b"%03d of %03.3lld"),
            ],
        )

        self.assertEquals(
            cursor.execute("select * from replaced_params").fetchall(),
            [
                (1, 1, 1, 0, b"%03d" ),
                (2, 1, 1, 1, b"%03.3lld"),
            ],
        )

        db.disconnect()

    @mock.patch.object(os.path, "abspath")
    def test_update_from_vcs(self, mock_function):
        mock_function.return_value = "some_full_path"
        vcs = mock.Mock()
        db = database.SQLite("some_filename")
        submodule_path = "submodule"

        db.update_from_vcs(vcs, submodule_path)

        vcs.add_file.assert_called_with("some_full_path", submodule_path)

    @mock.patch.object(os.path, "exists")
    def test_connect_loads_schema_if_new_database(self, mock_function):
        mock_function.return_value = False
        db = database.SQLite("some_filename")
        db._save_database = mock.Mock()

        orig_load_schema = db._load_schema
        db._load_schema = mock.Mock(side_effect = orig_load_schema)

        db._schema_file = mock.Mock(
            return_value = StringIO("""create table test_table (
                test_column INTEGER NOT NULL
            );""")
        )

        db.connect()

        db._load_schema.assert_called_with()

        cursor = db.dbh.cursor()
        cursor.execute("insert into test_table (test_column) values(1)")
        cursor.close()

        db.disconnect()

    @mock.patch.object(os.path, "exists")
    def test_connect_loads_existing_database(self, mock_function):
        mock_function.return_value = True
        db = database.SQLite("some_filename")

        def _connect(*args, **kwargs):
            db.dbh = sqlite3.connect(":memory:")

        def _disconnect(*args, **kwargs):
            db.dbh.close()

        db._connect = mock.Mock(side_effect = _connect)
        db.disconnect = mock.Mock(side_effect = _disconnect)

        orig_load_database = db._load_database
        db._load_database = mock.Mock(side_effect = orig_load_database)

        db._open_for_reading = mock.Mock(
            return_value = StringIO("""create table test_table (
                test_column INTEGER NOT NULL
            );

            insert into test_table(test_column) values(1);
            """)
        )

        db.connect()

        db._load_database.assert_called_with()
        db._open_for_reading.assert_called_with("some_filename")

        cursor = db.dbh.cursor()
        cursor.execute("select test_column from test_table")

        self.assertEquals(cursor.fetchall(), [(1,)])
        cursor.close()

        db.disconnect()

    def test_disconnect_saves_existing_database(self):
        db = database.SQLite("some_filename")

        def _connect(*args, **kwargs):
            db.dbh = sqlite3.connect(":memory:")

        lines = []
        def _write(line):
            lines.append(line)

        db.connect = mock.Mock(side_effect = _connect)

        output_file = mock.Mock()
        output_file.write = mock.Mock(side_effect = _write)
        db._open_for_writing = mock.Mock(return_value = output_file)
        db._remove_temporary_file = mock.Mock()

        db.connect()
        cursor = db.dbh.cursor()
        cursor.execute(
            "create table test_table (test_column INTEGER NOT NULL);"
        )
        cursor.execute("insert into test_table (test_column) values(1);")

        db.disconnect()

        db._open_for_writing.assert_called_with("some_filename")
        db._remove_temporary_file.assert_called_with()
        self.assertEquals(
            "".join(lines),
            """BEGIN TRANSACTION;
            CREATE TABLE test_table (test_column INTEGER NOT NULL);
            INSERT INTO "test_table" VALUES(1);
            COMMIT;
            """.replace("    ", "")
        )

    def test_remove_old_unmapped_strings(self):
        db = database.SQLite("some_filename")

        def _connect(*args, **kwargs):
            db.dbh = sqlite3.connect(":memory:")

        def _disconnect(*args, **kwargs):
            db.dbh.close()

        db._connect = mock.Mock(side_effect = _connect)
        db.disconnect = mock.Mock(side_effect = _disconnect)

        db.connect()
        db.write_string_mapping_for_platform(
            "Mac",
            {
                "SomeString" : "Translation for some string",
                "OtherString" : "Translation for some other string",
            }
        )

        cursor = db.dbh.cursor()
        self.assertEquals(
            cursor.execute("""
                select translation_key_no, translation_key
                from translation_keys"""
            ).fetchall(),
            [
                (2, b"OtherString"),
                (1, b"SomeString")
            ],
        )

        cursor.execute("""
            delete from native_translations
            where translation_key_no = 1
        """)

        db.remove_old_unmapped_strings()

        self.assertEquals(
            cursor.execute("""
                select translation_key_no, translation_key
                from translation_keys"""
            ).fetchall(),
            [
                (2, b"OtherString"),
                (1, b"SomeString")
            ],
        )

        cursor.execute("""
            update translation_keys
            set last_updated = datetime('now', '-89 days')
        """)

        db.remove_old_unmapped_strings()

        self.assertEquals(
            cursor.execute("""
                select translation_key_no, translation_key
                from translation_keys"""
            ).fetchall(),
            [
                (2, b"OtherString"),
                (1, b"SomeString")
            ],
        )

        cursor.execute("""
            update translation_keys
            set last_updated = datetime('now', '-91 days')
        """)

        db.remove_old_unmapped_strings()

        self.assertEquals(
            cursor.execute("""
                select translation_key_no, translation_key
                from translation_keys"""
            ).fetchall(),
            [
                (2, b"OtherString")
            ],
        )

        db.disconnect()

    def test_get_platforms(self):
        db = database.SQLite("some_filename")

        def _connect(*args, **kwargs):
            db.dbh = sqlite3.connect(":memory:")

        def _disconnect(*args, **kwargs):
            db.dbh.close()

        db._connect = mock.Mock(side_effect = _connect)
        db.disconnect = mock.Mock(side_effect = _disconnect)

        db.connect()
        db.write_string_mapping_for_platform(
            "Mac",
            {
                u"SomeString" : u"Mac translation for some string",
                u"OtherString" : u"Mac translation for some other string",
            }
        )

        db.write_string_mapping_for_platform(
            "Win",
            {
                u"SomeString" : u"Win translation for some string",
                u"OtherString" : u"Win translation for some other string",
            }
        )

        self.assertEquals(db.get_platforms(), [ u"Mac", u"Win" ])

        db.disconnect()

    def test_get_string_mapping_for_platform(self):
        db = database.SQLite("some_filename")

        def _connect(*args, **kwargs):
            db.dbh = sqlite3.connect(":memory:")

        def _disconnect(*args, **kwargs):
            db.dbh.close()

        db._connect = mock.Mock(side_effect = _connect)
        db.disconnect = mock.Mock(side_effect = _disconnect)

        db.connect()
        db.write_string_mapping_for_platform(
            "Mac",
            {
                u"SomeString" : u"Mac translation for some string",
                u"OtherString" : u"Mac translation for some other string",
            }
        )

        db.write_string_mapping_for_platform(
            "Win",
            {
                u"SomeString" : u"Win translation for some string",
                u"OtherString" : u"Win translation for some other string",
            }
        )

        self.assertEquals(
            db.get_string_mapping_for_platform("Mac"),
            {
                u"SomeString" : u"Mac translation for some string",
                u"OtherString" : u"Mac translation for some other string",
            }
        )

        self.assertEquals(
            db.get_string_mapping_for_platform("Win"),
            {
                u"SomeString" : u"Win translation for some string",
                u"OtherString" : u"Win translation for some other string",
            }
        )

        db.disconnect()

    def test_get_all_translation_keys(self):
        db = database.SQLite("some_filename")

        def _connect(*args, **kwargs):
            db.dbh = sqlite3.connect(":memory:")

        def _disconnect(*args, **kwargs):
            db.dbh.close()

        db._connect = mock.Mock(side_effect = _connect)
        db.disconnect = mock.Mock(side_effect = _disconnect)

        db.connect()
        db.write_string_mapping_for_platform(
            "Mac",
            {
                u"SomeString" : u"Mac translation for some string",
                u"OtherString" : u"Mac translation for some other string",
            }
        )

        self.assertEquals(
            db.get_all_translation_keys(),
            [ u"OtherString", u"SomeString", ],
        )

        db.disconnect()

    def test_get_all_native_translations(self):
        db = database.SQLite("some_filename")

        def _connect(*args, **kwargs):
            db.dbh = sqlite3.connect(":memory:")

        def _disconnect(*args, **kwargs):
            db.dbh.close()

        db._connect = mock.Mock(side_effect = _connect)
        db.disconnect = mock.Mock(side_effect = _disconnect)

        db.connect()
        db.write_string_mapping_for_platform(
            "Mac",
            {
                u"SomeString" : u"Mac translation for some string",
                u"OtherString" : u"Mac translation for some other string"
            }
        )

        self.assertEquals(
            db.get_all_native_translations(),
            [
                u"Mac translation for some string",
                u"Mac translation for some other string"
            ],
        )

        db.disconnect()

    def test_get_native_translations_for_platform(self):
        db = database.SQLite("some_filename")

        def _connect(*args, **kwargs):
            db.dbh = sqlite3.connect(":memory:")

        def _disconnect(*args, **kwargs):
            db.dbh.close()

        db._connect = mock.Mock(side_effect = _connect)
        db.disconnect = mock.Mock(side_effect = _disconnect)
        db._get_current_time = mock.Mock(
            return_value = "datetime('2010-12-02 02:20:00')"
        )

        db.connect()
        db.write_string_mapping_for_platform(
            "Mac",
            { "SomeString" : "%03d of %03.3lld for {0} %@", }
        )

        self.assertEquals(
            db.get_native_translations_for_platform("Mac"),
            [ "%03d of %03.3lld for {0} %@" ]
        )

        db.disconnect()

    @mock.patch("builtins.open")
    def test_open_for_reading(self, open_func):
        db = database.SQLite("some_filename")
        db._open_for_reading("filename")

        open_func.assert_called_with("filename", "r")

    @mock.patch.object(codecs, "open")
    def test_open_for_writing(self, open_func):
        db = database.SQLite("some_filename")
        db._open_for_writing("filename")

        open_func.assert_called_with("filename", "w", "utf-8")

    @mock.patch.object(os.path, "exists")
    def test_deletes_existing_temp_file_on_connect(self, exists_func):
        exists_func.return_value = True

        db = database.SQLite("some_filename")
        db._remove_temporary_file = mock.Mock()
        db._load_database         = mock.Mock()

        db.connect()

        db._remove_temporary_file.assert_called_with()
