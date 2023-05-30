#! /bin/python3
import logging
import os
import pprint
import re
import sys
import time

from selenium import webdriver
from selenium.webdriver.common.by import By


def download_image_even_when_forbidden(url, file_name):
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    img_element = driver.find_element(By.TAG_NAME, "img")
    with open(file_name, "wb") as file:
        file.write(img_element.screenshot_as_png)
    driver.quit()


TOKEN_PATH = "token.json"
APP_NAME = "ShikimoriToz"
CLIENT_ID = "5GufR7epCg2Wr9QKVyfC8wVv51SAi8o2iHPavcrQ3k4"
CLIENT_SECRET = "ckMcJpsJOubv4raN7hlaz1jIkLxTl7hT08OUYDzEGCc"

MAX_RETRIES = 1000
OUTPUT_FILE = "ranobes.json"
SORT_ORDER = "ranked"

from shikimori_api import Shikimori
import json
from requests.exceptions import HTTPError
from requests.models import Response


def token_saver(token: dict):
    with open('token.json', 'w') as f:
        f.write(json.dumps(token))


def load_token(path: str):
    with open(path) as f:
        return json.load(f)


def get_api(app_name: str, client_id: str, client_secret: str, token_path: str, token_saver):
    session = Shikimori(app_name,
                        client_id=client_id,
                        client_secret=client_secret,
                        token=load_token(token_path),
                        token_saver=token_saver)
    return session.get_api()


def get_ranobes(api, limit: int = 50, offset: int = 0, order: str = "ranked"):
    return api.ranobe.GET(limit=50, order=order, offset=offset)


def get_many_ranobes(api, pages: int = 6, order: str = "ranked"):
    ranobes = []
    for i in range(pages):
        fetched = False
        for j in range(MAX_RETRIES):
            try:
                ranobes += get_ranobes(api, limit=50, offset=i * 50, order=order)
                fetched = True
                break
            except HTTPError as e:
                response: Response = e.response
                if response.status_code == 429:
                    continue
                else:
                    print(f"Unknown error: {response.status_code}, {response.content}")
                    exit(1)
        if not fetched:
            print(f"Failed to fetch ranobe page with number {i}")
    return ranobes


def to_idtf(st):
    return (st
            .lower()
            .replace("!", "")
            .replace(".", "")
            .replace(" ", "_")
            .replace("-", "")
            .replace("'", "")
            .replace(",", "")
            .replace(":", ""))


def to_char_idtf(st):
    return (st
            .replace("!", "")
            .replace(".", "")
            .replace(" ", "_")
            .replace("-", "")
            .replace("'", "")
            .replace(",", "")
            .replace(":", ""))


def generate_main_scs(ranobe, roles):
    sys_idtf = "ranobe_" + to_idtf(ranobe["name"])
    russian_name = ranobe["russian"]
    english_name = ranobe["name"]

    print(f"Anime name is {english_name}.")

    genres = ranobe["genres"]
    genres = map(lambda x: x["name"], genres)
    genres = map(lambda x: "<- genre_" + to_idtf(x) + ";", genres)
    genres = list(genres)

    year = ranobe["aired_on"][:4]

    author = filter(lambda x: "Story" in x["roles"], roles)
    author = "person_" + to_char_idtf(list(author)[0]["person"]["name"])

    illustrator = filter(lambda x: "Art" in x["roles"], roles)
    illustrator = "person_" + to_char_idtf(list(illustrator)[0]["person"]["name"])

    print("Processed genres, illustrators, year...")

    main_characters = filter(lambda x: "Main" in x["roles"], roles)
    main_characters = map(lambda x: "-> rrel_main_character: char_" + to_char_idtf(x["character"]["name"]), main_characters)
    main_characters = list(main_characters)

    supporting_characters = filter(lambda x: "Supporting" in x["roles"], roles)
    supporting_characters = map(lambda x: "-> char_" + to_char_idtf(x["character"]["name"]), supporting_characters)
    supporting_characters = list(supporting_characters)[:5]

    with open("template.scst") as template_file:
        template = template_file.read()
        template = template.replace("${SYS_IDTF}", sys_idtf)
        template = template.replace("${RUSSIAN_NAME}", russian_name)
        template = template.replace("${ENGLISH_NAME}", english_name)
        template = template.replace("${GENRES}", "\n    ".join(genres))
        template = template.replace("${AUTHOR_IDTF}", author)
        template = template.replace("${ILLUSTRATOR_IDTF}", illustrator)
        template = template.replace("${YEAR}", year)
        template = template.replace("${MAIN_CHAR_IDTF}", ";;\n            ".join(main_characters))
        template = template.replace("${OTHER_CHARS}", ";;\n            ".join(supporting_characters))

    print("Main SCs file created...")

    if not os.path.exists(sys_idtf):
        os.mkdir(sys_idtf)
    if not os.path.exists(sys_idtf + "/content"):
        os.mkdir(sys_idtf + "/content")
    if not os.path.exists(sys_idtf + "/images"):
        os.mkdir(sys_idtf + "/images")
    if not os.path.exists(sys_idtf + "/authors"):
        os.mkdir(sys_idtf + "/authors")

    description = ranobe["description"]
    description = re.sub(r"\[.*\]", "", description)
    with open(sys_idtf + "/content/description.html", "w") as file:
        file.write("<p>" + description + "</p>")

    print("Downloading cover...")

    image_link = "https://shikimori.one/" + ranobe["image"]["original"]
    download_image_even_when_forbidden(image_link, sys_idtf + "/images/cover.jpg")

    with open(sys_idtf + "/" + sys_idtf + ".scs", "w") as result:
        result.write(template)

    return sys_idtf, russian_name


characters_cache = {}


def get_character_with_delay(api, id):
    if id in characters_cache.keys():
        return characters_cache[id]

    time.sleep(0.2)
    char = api.characters(id).GET()
    characters_cache[char["id"]] = char

    print(f"Getting character {char['name']}")

    return char


def generate_characters(api, roles, ranobe_idtf, ranobe_name):
    main_characters = filter(lambda x: "Main" in x["roles"], roles)
    main_characters = list(main_characters)[:10]
    main_characters = map(lambda x: x["character"], main_characters)
    main_characters = map(lambda x: get_character_with_delay(api, x["id"]), main_characters)
    main_characters = list(main_characters)

    supporting_characters = filter(lambda x: "Supporting" in x["roles"], roles)
    supporting_characters = list(supporting_characters)[:5]
    supporting_characters = map(lambda x: x["character"], supporting_characters)
    supporting_characters = map(lambda x: get_character_with_delay(api, x["id"]), supporting_characters)
    supporting_characters = list(supporting_characters)

    result = ""

    for char in main_characters + supporting_characters:
        sys_idtf = "char_" + to_char_idtf(char["name"])
        race = "person"
        sex = "male"
        english_name = char["name"]
        russian_name = char["russian"]

        image_link = "https://shikimori.one/" + char["image"]["original"]
        download_image_even_when_forbidden(image_link, ranobe_idtf + "/images/" + sys_idtf + ".jpg")

        try:
            description = char["description"] \
                .replace("[br]", "<br>") \
                .replace("[spoiler=спойлер]", "") \
                .replace("[/spoiler]", "") \
                .replace("[/character]", "")
            description = re.sub(r"\[character=\d+\]", "", description)
        except:
            description = f"{russian_name} - персонаж ранобе {ranobe_name}"

        with open(ranobe_idtf + "/content/" + sys_idtf + ".html", "w") as file:
            file.write("<p>" + description + "</p>")

        with open("char_template.scst") as template_file:
            template = template_file.read()
            template = template.replace("${SYS_IDTF}", sys_idtf)
            template = template.replace("${RUSSIAN_NAME}", russian_name)
            template = template.replace("${ENGLISH_NAME}", english_name)
            template = template.replace("${RACE}", race)
            template = template.replace("${SEX}", sex)

        result += template

    with open(ranobe_idtf + "/" + ranobe_idtf + "_characters.scs", 'w') as file:
        file.write(result)


def generate_authors(ranobe_idtf, ranobe, roles):

    print("Generating author...")

    genres = ranobe["genres"]
    genres = map(lambda x: x["name"], genres)
    genres = map(lambda x: "-> genre_" + to_idtf(x) + ";;", genres)
    genres = list(genres)

    author = filter(lambda x: "Story" in x["roles"], roles)
    author = list(author)[0]["person"]
    sys_idtf = "person_" + to_char_idtf(author["name"])
    russian_name = author["russian"]
    english_name = author["name"]

    with open("author_template.scst") as template_file:
        template = template_file.read()
        template = template.replace("${SYS_IDTF}", sys_idtf)
        template = template.replace("${RUSSIAN_NAME}", russian_name)
        template = template.replace("${ENGLISH_NAME}", english_name)
        template = template.replace("${GENRES}", "\n            ".join(genres))

    with open(f"{ranobe_idtf}/authors/{ranobe_idtf}_author.scs", "w") as file:
        file.write(template)

    print("Generating illustrator...")

    author = filter(lambda x: "Art" in x["roles"], roles)
    author = list(author)[0]["person"]
    sys_idtf = "person_" + to_char_idtf(author["name"])
    russian_name = author["russian"]
    english_name = author["name"]

    with open("illustrator_template.scst") as template_file:
        template = template_file.read()
        template = template.replace("${SYS_IDTF}", sys_idtf)
        template = template.replace("${RUSSIAN_NAME}", russian_name)
        template = template.replace("${ENGLISH_NAME}", english_name)
        template = template.replace("${GENRES}", "\n            ".join(genres))

    with open(f"{ranobe_idtf}/authors/{ranobe_idtf}_illustrator.scs", "w") as file:
        file.write(template)


def generate_fragment(id):
    print(f"Fetching data for anime {id}")
    api = get_api(APP_NAME, CLIENT_ID, CLIENT_SECRET, TOKEN_PATH, token_saver)
    ranobe = api.ranobe(id).GET()
    roles = api.ranobe(id).roles.GET()

    dir_name, ranobe_name = generate_main_scs(ranobe, roles)
    generate_characters(api, roles, dir_name, ranobe_name)
    generate_authors(dir_name, ranobe, roles)

    print("Done!")


if __name__ == "__main__":
    generate_fragment(sys.argv[1])