import random
import unittest

from io import BytesIO

from burton import translation

class XLFTests(unittest.TestCase):
    test_xlf = str.encode("""<?xml version='1.0' encoding='UTF-8'?>
<xliff version="1.0">
  <file build-num="AG3 doesn't specify" category="" product-name="Test Product" source-language="en" target-language="Italian">
    <header>
      <phase-group>
        <phase company-name="Test Company" contact-email="foo@example.com" contact-phone="" phase-name="test num" process-name="Translations entered by 'test num'" tool="LocFactory Editor"/>
      </phase-group>
    </header>
    <!--...................................................-->
    <body>
      <group resname="Group Name">
        <trans-unit restype="string">
          <source xml:lang="en">Some untranslated string {0}</source>
          <target/>
        </trans-unit>
        <trans-unit restype="string">
          <source xml:lang="en">Some translated string</source>
          <target>Traduzione di Bablefish per questa stringa</target>
        </trans-unit>
      </group>
    </body>
  </file>
</xliff>
""")

    sorted_test_xlf = str.encode("""<?xml version='1.0' encoding='UTF-8'?>
<xliff version="1.0">
  <file build-num="AG3 doesn't specify" category="" product-name="Test Product" source-language="en" target-language="Italian">
    <header>
      <phase-group>
        <phase company-name="Test Company" contact-email="foo@example.com" contact-phone="" phase-name="test num" process-name="Translations entered by 'test num'" tool="LocFactory Editor"/>
      </phase-group>
    </header>
    <!--...................................................-->
    <body>
      <group resname="Group Name">
        <trans-unit restype="string">
          <source xml:lang="en">X</source>
          <target/>
        </trans-unit>
        <trans-unit restype="string">
          <source xml:lang="en">Y</source>
          <target/>
        </trans-unit>
        <trans-unit restype="string">
          <source xml:lang="en">Z</source>
          <target/>
        </trans-unit>
        <trans-unit restype="string">
          <source xml:lang="en">A</source>
          <target>9</target>
        </trans-unit>
        <trans-unit restype="string">
          <source xml:lang="en">B</source>
          <target>8</target>
        </trans-unit>
        <trans-unit restype="string">
          <source xml:lang="en">C</source>
          <target>7</target>
        </trans-unit>
      </group>
    </body>
  </file>
</xliff>
""")

    def test_read(self):
        trans = translation.XLF("Italian", "it-IT", "en", "", "", "")
        file = BytesIO(XLFTests.test_xlf)

        trans.read(file)
        file.close()

        self.assertEquals(
            trans.translation_dict,
            {
                "Some untranslated string {0}" : None,
                u"Some translated string" :
                    u"Traduzione di Bablefish per questa stringa",
                u"Some translated string..." :
                    u"Traduzione di Bablefish per questa stringa...",
                u"Some translated string\xe2\x80\xa6" :
                    u"Traduzione di Bablefish per questa stringa\xe2\x80\xa6"
            }
        )

    def test_write(self):
        trans = translation.XLF(
            "Italian",
            "it-IT",
            "en",
            "Test Company",
            "Test Product",
            "foo@example.com"
        )

        trans.add_translation(
            u"Some translated string",
            u"Traduzione di Bablefish per questa stringa"
        )

        trans.add_translation("Some untranslated string %d", None)

        file = BytesIO()
        trans.write(file)

        self.assertEquals(file.getvalue(), XLFTests.test_xlf)
        file.close()

    def test_sorts_by_key__untranslated_first__when_writing(self):
        trans = translation.XLF(
            "Italian",
            "it-IT",
            "en",
            "Test Company",
            "Test Product",
            "foo@example.com"
        )

        mappings = [
            { "A" : "9"  },
            { "B" : "8"  },
            { "C" : "7"  },
            { "X" : None },
            { "Y" : None },
            { "Z" : None },
        ]

        random.shuffle(mappings)
        for mapping in mappings:
            for key, value in mapping.items():
                trans.add_translation(key, value)

        file = BytesIO()

        trans.write(file)

        self.assertEquals(file.getvalue(), XLFTests.sorted_test_xlf)
        file.close()
