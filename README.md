# anagrammihaku
Tässä on yksinkertainen anagrammikone joka vertailee tietokannasta sanoja ja etsii niiden anagrammeja.
Kyseessä on yksinkertainen Python-ohjelma ja itse olen ajanut sitä Fast-Api frameworkillä.

Tässä Gitissä on mukana peruskoodi. Tietokanta ei ole mukana, mutta mukana on txt-tiedosto, jossa on sanat joilla tietokanta populoidaan.

Tietokannassa on sarakkeet "word" ja "sorted_word". Ensimmäinen sarake täytetään tuon tekstitiedoston sanoilla.
Toinen sarake täytetään tällä kyselyllä:

ALTER TABLE words ADD COLUMN sorted_word VARCHAR(50);
UPDATE words SET sorted_word = (SELECT GROUP_CONCAT(CHAR) FROM (SELECT SUBSTRING_INDEX(SUBSTRING_INDEX(word, '', n), '', -1) AS CHAR FROM numbers WHERE n <= CHAR_LENGTH(word) ORDER BY CHAR) AS temp);

Jos ei tuo kysely toimi, niin sitten muistin väärin :)

Sen jälkeen vaan kokeilemaan ja parantelemaan ratkaisua. Tämä osaa hakea täydellisiä anagrammeja ja sellaisia jotka koostuvat kahdesta tai kolmesta sanasta. Jos sellaista ei löydy johon kaikki kirjaimet sopivat se palauttaa virhe-ilmoituksen. Sanastossa on noin 90 000 suomenkielen sanaa perusmuodossa, eli sanoja jotka löytyvät kielitoimiston sanakirjasta.
Kenttä "Sanan tarkistus" hakee vain sanaa sanastosta, eli sillä voit tarkistaa onko kyseessä perusmuotoinen suomenkielen sana.


VINKKI: Sanaa jonka kirjoitat hakuun ei tarkisteta sanastosta, eli voit kokeilla vaikka hassuja lauseita ja mitä vaan ilmauksia. Erikoismerkit ym. soo-soo jutut sieltä siivotaan pois.
