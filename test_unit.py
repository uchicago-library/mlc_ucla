import click, local, os, sqlite3, sqlite_dump, unittest, utils

class TestMLCDB(unittest.TestCase):
    mlc_db = utils.MLCDB({
        'DB': 'test.sql',
        'GLOTTO_TRIPLES': 'data/glottolog_language.ttl',
        'MESO_TRIPLES': 'test_data/test.ttl',
        'TGN_TRIPLES': 'data/tgn.ttl'
    })

    def test_list_items(self):
        self.assertEqual(
	    sorted(self.__class__.mlc_db.get_item_list()),
            [
                'https://ark.lib.uchicago.edu/ark:61001/s1_i1',
                'https://ark.lib.uchicago.edu/ark:61001/s1_i2',
                'https://ark.lib.uchicago.edu/ark:61001/s1_i3', 
                'https://ark.lib.uchicago.edu/ark:61001/s2_i1',
                'https://ark.lib.uchicago.edu/ark:61001/s2_i2',
                'https://ark.lib.uchicago.edu/ark:61001/s2_i3'
            ]
        )

    def test_list_series(self):
        self.assertEqual(
	    sorted(self.__class__.mlc_db.get_series_list()),
            [
                'https://ark.lib.uchicago.edu/ark:61001/s1',
                'https://ark.lib.uchicago.edu/ark:61001/s2'
            ]
        )

    def test_contributor_browse(self):
        self.assertEqual(
            self.__class__.mlc_db.get_browse('contributor'),
            [
                ('contributor one', 1),
                ('contributor two', 1)
            ]
        )

    def test_creator_browse(self):
        self.assertEqual(
            self.__class__.mlc_db.get_browse('creator'),
            [
                ('interviewer one', 1), 
                ('interviewer three', 1), 
                ('interviewer two', 1)
            ]
        )

    def test_date_browse(self):
        self.assertEqual(
            self.__class__.mlc_db.get_browse('date'),
            [
                ('1979/2018', 2)
            ]
        )

    def test_decade_browse(self):
        self.assertEqual(
            self.__class__.mlc_db.get_browse('decade'),
            [
                ('1970s', 2), 
                ('1980s', 2), 
                ('1990s', 2), 
                ('2000s', 2), 
                ('2010s', 2)
            ]
        )

    def test_language_browse(self):
        self.assertEqual(
            self.__class__.mlc_db.get_browse('language'),
            [
                ('English', 2), 
                ('Spanish', 2),
                ('Yucatec Maya', 2)
            ]
        )

if __name__=='__main__':
    unittest.main()
