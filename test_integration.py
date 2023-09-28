import click, unittest, urllib.parse
from app import app, cli_get_browse, cli_list_items, cli_list_series
from click.testing import CliRunner


class TestMLCCLI(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()

    # browse 
    def test_browse(self):
        for b in ('contributor', 'creator', 'date', 'decade', 'language'):
            self.assertEqual(
                self.runner.invoke(cli_get_browse, [b]).exit_code,
                0
            )

    # list items
    def test_list_item(self):
        self.assertEqual(
            self.runner.invoke(cli_list_items).exit_code,
            0
        )
        self.assertEqual(
            self.runner.invoke(cli_list_items, ['--verbose']).exit_code,
            0
        )

    # list series
    def test_list_series(self):
        self.assertEqual(
            self.runner.invoke(cli_list_series).exit_code,
            0
        )
        self.assertEqual(
            self.runner.invoke(cli_list_series, ['--verbose']).exit_code,
            0
        )


class TestMLCSite(unittest.TestCase):
    def setUp(self):
        self.ctx = app.app_context()
        self.ctx.push()
        self.client = app.test_client()

    def tearDown(self):
        self.ctx.pop()

    def test_home(self):
        self.assertEqual(self.client.get('/').status_code, 200)

    def test_search(self):
        # no query.
        self.assertEqual(self.client.get('/search/').status_code, 200)

        # search term that appears in many records. 
        self.assertEqual(
            self.client.get('/search/?query=spanish').status_code,
            200
        )

        # search term includes a comma.
        self.assertEqual(
            self.client.get('/search/?query=San+Cristobal%2C+Totonicapan').status_code,
            200
        )

        # search terms include special characters.
        for q in ('IOUgf)&T *Q&V*)@#Y V$*(Y@*(Y(P@*Y@*(PY *(P@*(PY@*( YP(@Y )(* @UYP* UY@',
                  '()&*@#$', '()', '?', '/', '`'):
            self.assertEqual(
                self.client.get(
                    '/search/?query={}'.format(
                        urllib.parse.quote_plus(q)
                    )
                ).status_code,
                200
            )

        # a search with many tokens.
        self.assertEqual(
            self.client.get('/search/?query=a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+++++aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+++++a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+++++a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+++++a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+++++a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+++++a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+++++aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+a++++a+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+++++a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+++++a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+++++a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+++++a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+++++a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+++++aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+a').status_code,
 200
        )

        # representative searches from DB.
        for q in ('vasquez', 'fernandez', 'smith', 'charles', 'penninsula',
                  'recordings', 'Maya recordings', 'K\'iche\'', 
                  'K\'iche\' dialect survey', 'Zapotec',
                  'Tlaxcala-Puebla-Central Nahuatl', 'Field recordings',
                  'Spoken language', 'Vocabulary', 'mopan vocabulary',
                  'Aluminum discs', 'Guatemala texts', 'Mam speakers', 
                  'Chants and folk songs', 'Male informant', 
                  'Honduras music', 'Man-in-nature project', 'Chiapas Project',
                  'Microfilm Collection of Manuscripts on Cultural Anthropology', 
                  'Mexican folktales', 'Huichol chants', 'Norman McQuown',
                  'Manuel Andrade', 'González, Raul', 'Tampemoch', 'Veracruz',
                  'Chiapas', 'Distrito Federal', 'Interviews in Belize'):
            self.assertEqual(
                self.client.get(
                    '/search/?query={}'.format(
                        urllib.parse.quote_plus(q)
                    )
                ).status_code,
                200
            )

        # representative searches from JL.
        for q in ('Isthmus Zapotec', 'Isthmus Nahuatl'):
            self.assertEqual(
                self.client.get(
                    '/search/?query={}'.format(
                        urllib.parse.quote_plus(q)
                    )
                ).status_code,
                200
            )


if __name__=='__main__':
    unittest.main()
