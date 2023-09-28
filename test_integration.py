import click, local, os, sqlite3, sqlite_dump, unittest, utils

from app import app

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

        # search term includes special characters.
        self.assertEqual(
            self.client.get('/search/?query=IOUgf%29%26T+*Q%26V*%29%40%23Y+V%24*%28Y%40*%28Y%28P%40*Y%40*%28PY+*%28P%40*%28PY%40*%28+YP%28%40Y+%29%28*+%40UYP*+UY%40').status_code,
            200
        )

        self.assertEqual(
            self.client.get('/search/?query=%28%29%26*%40%23%24').status_code,
            200
        )

        self.assertEqual(
            self.client.get('/search/?query=%28%29').status_code,
            200
        )

        self.assertEqual(
            self.client.get('/search/?query=%3F').status_code,
            200
        )

        self.assertEqual(
            self.client.get('/search/?query=%2F').status_code,
            200
        )

        self.assertEqual(
            self.client.get('/search/?query=%60').status_code,
            200
        )

        self.assertEqual(
            self.client.get('/search/?query=a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+++++aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+++++a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+++++a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+++++a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+++++a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+++++a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+++++aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+a++++a+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+++++a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+++++a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+++++a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+++++a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+++++a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+++++aa+a+a+a+a+a+aa+a+a+a+a+a+aa+a+a+a+a+a+a').status_code,
 200
        )

        # representative searches from DB.

        self.assertEqual(
            self.client.get('/search/?query=vasquez').status_code,
            200
        )

        self.assertEqual(
            self.client.get('/search/?query=fernandez').status_code,
            200
        )

        self.assertEqual(
            self.client.get('/search/?query=smith').status_code,
            200
        )

        self.assertEqual(
            self.client.get('/search/?query=charles').status_code,
            200
        )

        self.assertEqual(
            self.client.get('/search/?query=penninsula').status_code,
            200
        )

        self.assertEqual(
            self.client.get('/search/?query=Maya+recordings').status_code,
            200
        )

        self.assertEqual(
            self.client.get('/search/?query=Maya+recordings').status_code,
            200
        )

        self.assertEqual(
            self.client.get('/search/?query=K%27iche%27').status_code,
            200
        )

        self.assertEqual(
            self.client.get('/search/?query=K%27iche%27+dialect+survey').status_code,
            200
        )

        self.assertEqual(
            self.client.get('/search/?query=Zapotec').status_code,
            200
        )

        self.assertEqual(
            self.client.get('/search/?query=Tlaxcala-Puebla-Central+Nahuatl').status_code,
            200
        )

        self.assertEqual(
            self.client.get('/search/?query=Field+recordings').status_code,
            200
        )

        self.assertEqual(
            self.client.get('/search/?query=Spoken+language').status_code,
            200
        )

        self.assertEqual(
            self.client.get('/search/?query=Vocabulary').status_code,
            200
        )

        self.assertEqual(
            self.client.get('/search/?query=mopan+vocabulary').status_code,
            200
        )

        self.assertEqual(
            self.client.get('/search/?query=Aluminum+discs').status_code,
            200
        )

        self.assertEqual(
            self.client.get('/search/?query=Guatemala+texts').status_code,
            200
        )

        self.assertEqual(
            self.client.get('/search/?query=Mam+speakers').status_code,
            200
        )

        self.assertEqual(
            self.client.get('/search/?query=Chants+and+folk+songs').status_code,
            200
        )

        self.assertEqual(
            self.client.get('/search/?query=Male+informant').status_code,
            200
        )

        self.assertEqual(
            self.client.get('/search/?query=Honduras+music').status_code,
            200
        )

        self.assertEqual(
            self.client.get('/search/?query=Man-in-nature+project').status_code,
            200
        )

        self.assertEqual(
            self.client.get('/search/?query=Chiapas+Project').status_code,
            200
        )

        self.assertEqual(
            self.client.get('/search/?query=Microfilm+Collection+of+Manuscripts+on+Cultural+Anthropology').status_code,
            200
        )

        self.assertEqual(
            self.client.get('/search/?query=Mexican+folktales').status_code,
            200
        )

        self.assertEqual(
            self.client.get('/search/?query=Huichol+chants').status_code,
            200
        )

        self.assertEqual(
            self.client.get('/search/?query=Norman+McQuown').status_code,
            200
        )

        self.assertEqual(
            self.client.get('/search/?query=Manuel+Andrade').status_code,
            200
        )

        self.assertEqual(
            self.client.get('/search/?query=González%2C+Raul').status_code,
            200
        )

        self.assertEqual(
            self.client.get('/search/?query=Tampemoch').status_code,
            200
        )

        self.assertEqual(
            self.client.get('/search/?query=Veracruz').status_code,
            200
        )

        self.assertEqual(
            self.client.get('/search/?query=Chiapas').status_code,
            200
        )

        self.assertEqual(
            self.client.get('/search/?query=Distrito+Federal').status_code,
            200
        )

        self.assertEqual(
            self.client.get('/search/?query=Interviews+in+Belize').status_code,
            200
        )

        # representative searches from JL.

        self.assertEqual(
            self.client.get('/search/?query=Isthumus+Zapotec').status_code,
            200
        )

        self.assertEqual(
            self.client.get('/search/?query=Isthumus+Nahuatl').status_code,
            200
        )


if __name__=='__main__':
    unittest.main()
