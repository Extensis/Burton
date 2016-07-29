# Burton — A Framework For Managing Translations

Burton is a collection of Python 2 modules that assist in managing string translations across multiple projects. It was written at Extensis in 2010 to synchronize translation efforts between its OS X and Windows font management desktop applications. Since then, it has also been used in Flash and JavaScript projects.

At its core, Burton collects translatable strings from the source and resource files of multiple projects, storing them in a central database. When those strings are translated, it can then write localized resource files for each project. This allows developers to easily collect strings for translation, ensuring they don't miss any, and allows them to ensure that all translated strings are integrated into every project properly.

It can also check for errors in the original source and resource files. For example, on the Mac, if a string appears in a nib or in a call to `NSLocalizedString`, but does not appear in any .strings files, Burton will display a warning for that string.

Burton currently supports the following file formats.

* Objective-C/Objective-C++ source files
* Mac nib/xib/strings files
* Windows resx/rc files
* Properties files
* Angular JavaScript files

## Setup

Burton is very configurable, but it is not "batteries included". To use Burton, you will need to write short scripts to perform various actions. There are example scripts located in the `samples` directory which you can modify to fit your project.

In addition, if you are working with a file format not currently supported by Burton, you will need to create a parser subclass for that file format (more on that below).

### Repository Setup

The first step in setting up Burton is to set up a repository to store the central database for your strings. By default, Burton stores all strings in a SQLite database, and all translations in XLIFF files. Both types of files will live in this repository. When Burton runs, it will add new strings to both the database and the XLIFF files. When you are ready to localize your project, you edit the XLIFF files to add translated strings and run burton again. Burton will generate localized resource files for your projects.

When running burton, you will need to have both this repository and the burton repository, along with your project's repository, cloned onto the same machine.

### Script Setup

Once you have a separate repository for your string database and XLIFF files, you will need to copy `localize.py` and `burton.config.sample` from the scripts directory into the repository for your project, renaming `burton.config.sample` to `burton.config`. You will then need to edit both to point to the burton repository and your strings repository. The sample config file contains documentation for each of the settings in the file.

### Running

Burton may revert changes if it encounters errors, so make sure you have committed all changes before running Burton. You can start the process by running `python localize.py`. This will collect strings from your projects and write localized resource files to your project.

After Burton finishes, you can send the XLIFF files to translators. When you receive the translated XLIFF files back, You can place them into your repo, commit that repo, and then run `python localize.py` again.

If you are running this process from a build server, you can add a `--commit-vcs` flag to `python localize.py`. This will cause Burton to commit all changes and push them to `origin/HEAD`

### Creating a Parser Subclass

Support for new file formats can be added by creating a new parser subclass. 'burton/parser/resx.py' is probably the best template to start from. If you only need to read strings from files, you need to override the `extract_strings_from_filename` method. If you need to read string mappings from files (e.g. Mac .strings files or Angular .i18n.js files), you need to override `extract_mapping_from_filename`. If you need to write localized files, then you must override the `translate` method.

In addition to handling the reading and writing of files, these subclasses are responsible for adding any changes they make to source control.

After creating your subclass, you must add it to `burton/parser/__init__.py`.

## Contributing

If you write a parser subclass and believe it would be useful to others, please submit a pull request.

Burton is fairly well-tested, so and pull requests with tests are more likely to be accepted in a timely manner.

Having been in continuous use since 2010, Burton has needed very few changes over the years. However, it uses an older version of Python and many older libraries. While these could be updated, it is important that Burton remains able to run out of the box on macOS. Until Python 3 is bundled with macOS, it is important to maintain compatibility with Python 2.7.

## License

Burton is distributed under an MIT license. See LICENSE.md
