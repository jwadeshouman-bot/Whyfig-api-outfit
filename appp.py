from flask import Flask, request, send_file
import requests
from PIL import Image
from io import BytesIO
import os
import threading

app = Flask(__name__)
session = requests.Session()

API_KEY = "Whyfigage"
BACKGROUND_FILENAME = "outfit.png"
ICON_SIZE = (95, 95)

# ============================================================
# ✅ Games Kinbo API
# ============================================================
GAMESKINBO_URL = "https://api.gameskinbo.com/ff-info/get"
GAMESKINBO_API_KEY = "CZwkGnWw0TzJqqfU9RqV_dQ7SBZkmUxCZzABO38rQ7k"

HEX_POSITIONS = {
    "mask": (990, 420),
    "shirt": (190, 90),
    "pants": (40, 420),
    "shoes": (840, 90),
    "emote": (40, 230),
    "armor": (990, 230),
    "character": (600, 390),
    "weapon": (190, 560),
    "pet": (840, 560)
}

fallback_ids = ["211000000", "214000000", "208000000", "203000000", "204000000", "205000000", "212000000"]

def fetch_icon(icon_id):
    ids_to_try = []
    if icon_id and str(icon_id) != "0":
        ids_to_try.append(str(icon_id))
    for fid in fallback_ids:
        if fid not in ids_to_try:
            ids_to_try.append(fid)
    for i in ids_to_try:
        try:
            url = f"https://iconapi.wasmer.app/{i}"
            r = session.get(url, timeout=10)
            if r.status_code == 200:
                img = Image.open(BytesIO(r.content)).convert("RGBA")
                return img.resize(ICON_SIZE, Image.Resampling.LANCZOS)
        except:
            continue
    return None

@app.route('/outfit-image', methods=['GET'])
def outfit_image():
    uid = request.args.get('uid')
    key = request.args.get('key')
    region = request.args.get('region', 'BD')
    
    if key != API_KEY:
        return {"error": "Key Error"}, 401
    
    try:
        # ====== ✅ Games Kinbo API ======
        headers = {"x-api-key": GAMESKINBO_API_KEY}
        params = {"uid": uid, "region": region}
        response = session.get(GAMESKINBO_URL, headers=headers, params=params, timeout=15)
        
        if response.status_code != 200:
            return {"error": f"API Down ({response.status_code})"}, 500
        
        data = response.json()
        
        # ====== ✅ استخراج البيانات من الشكل الجديد ======
        equipped = data.get("EquippedItemsInfo", {})
        pet_info = data.get("PetInfo", {})
        
        outfit = equipped.get("EquippedOutfit", []) or []
        weapon_list = equipped.get("EquippedWeapon", []) or []
        
        # ====== مهام الرسم ======
        draw_tasks = {
            "mask":   outfit[0] if len(outfit) > 0 else None,
            "shirt":  outfit[1] if len(outfit) > 1 else None,
            "pants":  outfit[2] if len(outfit) > 2 else None,
            "shoes":  outfit[3] if len(outfit) > 3 else None,
            "emote":  outfit[4] if len(outfit) > 4 else None,
            "armor":  outfit[5] if len(outfit) > 5 else None,
            "weapon": weapon_list[0] if len(weapon_list) > 0 else None,
            "pet":    pet_info.get("skinId"),
            "character": None
        }
        
        # ====== رسم الصورة ======
        if not os.path.exists(BACKGROUND_FILENAME):
            return "File Not Found", 500
        
        canvas = Image.open(BACKGROUND_FILENAME).convert("RGBA")
        
        for slot, item_id in draw_tasks.items():
            if not item_id:
                continue
            
            icon_img = fetch_icon(item_id)
            if not icon_img:
                continue
            
            pos = HEX_POSITIONS.get(slot)
            if not pos:
                continue
            
            if slot == "character":
                icon_img = icon_img.resize((480, 480), Image.Resampling.LANCZOS)
                x, y = pos
                w, h = icon_img.size
                pos = (x - w // 2, y - h // 2)
            
            canvas.paste(icon_img, pos, icon_img)
        
        img_io = BytesIO()
        canvas.save(img_io, 'PNG')
        img_io.seek(0)
        
        return send_file(img_io, mimetype='image/png')
    
    except Exception as e:
        return {"error": str(e)}, 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)