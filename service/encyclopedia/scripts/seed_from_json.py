import json, uuid, os
from db import get_conn

DATA_PATH = os.getenv("SPECIES_JSON", "/data/species.json")

def pick(d, keys, default=None):
    for k in keys:
        if k in d and d[k] not in (None, ""):
            return d[k]
    return default

def main():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    # รองรับทั้ง list หรือ dict ที่มี key "items"
    if isinstance(data, dict):
        data = data.get("items") or data.get("data") or []

    conn = get_conn()
    inserted = 0
    with conn.cursor() as cur:
        for item in data:
            name_en = pick(item, ["name_en", "english_name", "name", "NameEN"])
            if not name_en:
                continue

            row = {
                "id": str(uuid.uuid4()),
                "name_en": name_en,
                "name_th": pick(item, ["name_th", "thai_name", "NameTH"]),
                "short_name": pick(item, ["short_name", "ShortName"]),
                "scientific_name": pick(item, ["scientific_name", "sci_name", "ScientificName"]),
                "group": pick(item, ["group", "category"], None),
                "venom_type": pick(item, ["venom_type", "venom"], None),
                "symptoms_th": pick(item, ["symptoms_th", "symptoms"], None),
                "habitat_th": pick(item, ["habitat_th", "habitat"], None),
                "first_aid_th": pick(item, ["first_aid_th", "first_aid"], None),
                "image_path": pick(item, ["image_path", "image", "img"], None),
                "sources": json.dumps(pick(item, ["sources"], []), ensure_ascii=False),
            }

            sql = """
              INSERT INTO snakes (
                id, name_en, name_th, short_name, scientific_name, `group`,
                venom_type, symptoms_th, habitat_th, first_aid_th, image_path, sources
              )
              VALUES (%(id)s,%(name_en)s,%(name_th)s,%(short_name)s,%(scientific_name)s,%(group)s,
                      %(venom_type)s,%(symptoms_th)s,%(habitat_th)s,%(first_aid_th)s,%(image_path)s,%(sources)s)
              ON DUPLICATE KEY UPDATE
                name_th=VALUES(name_th),
                short_name=VALUES(short_name),
                scientific_name=VALUES(scientific_name),
                `group`=VALUES(`group`),
                venom_type=VALUES(venom_type),
                symptoms_th=VALUES(symptoms_th),
                habitat_th=VALUES(habitat_th),
                first_aid_th=VALUES(first_aid_th),
                image_path=VALUES(image_path),
                sources=VALUES(sources)
            """
            cur.execute(sql, row)
            inserted += 1

    conn.close()
    print(f"Seed done. processed={inserted}")

if __name__ == "__main__":
    main()