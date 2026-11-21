"""
Spot The Difference Studio - Professional KDP AI Prompt Generator Engine
Generates tailored, high-converting image generation prompts for Midjourney, DALL-E 3, Flux, and Universal AI models.
Engineered specifically for children's activity books and optimized for Spot-the-Difference mechanics:
- Clean, crisp outline separation
- High contrast and flat saturated colors (perfect for Color Swap)
- Multiple isolated foreground objects (perfect for Erase, Clone, and Flip)
- Zero text, zero clutter, cheerful kid-friendly aesthetics
"""

import random
from typing import List, Dict, Any

# ---------------------------------------------------------------------------
# 1. WINTER & CHRISTMAS NICHE FOUNDATIONS
# ---------------------------------------------------------------------------

WINTER_CHRISTMAS_FOUNDATIONS = [
    {
        "title": "Santa's North Pole Toy Workshop",
        "setting": "inside Santa's cozy wooden North Pole workshop with timber rafters and warm glowing lanterns",
        "characters": "three cheerful little holiday elves in green and red tunics with bells on their curly pointed shoes",
        "action": "busy painting wooden toy trains, stitching button eyes onto teddy bears, and wrapping gift boxes with satin ribbons",
        "objects": "a wooden workbench with colorful paint jars (blue, yellow, purple), a carved rocking horse, a cuckoo wall clock, hanging holly garlands, and stacks of wrapped gift boxes with big bows",
        "suggested_diffs": [
            "🎨 Color Swap: Change the paint jar on the workbench from bright blue to yellow",
            "🧽 Erase: Remove the hanging holly garland on the top left beam",
            "🔄 Flip: Flip the wooden rocking horse to face left instead of right",
            "📋 Clone: Duplicate one of the small wrapped gift boxes on the floor"
        ]
    },
    {
        "title": "Penguin Friends Ice Skating on a Forest Pond",
        "setting": "a sparkling frozen forest pond surrounded by snow-dusted evergreen fir trees and white hills",
        "characters": "four adorable chubby baby penguins wearing colorful knitted wool scarves, earmuffs, and pom-pom beanies",
        "action": "gliding happily across smooth ice, one penguin doing a gentle spin, another sliding on its belly, and one pushing a wooden sled",
        "objects": "a red thermos flask, a wooden park bench with two steaming mugs of hot cocoa, a cute red robin bird perched on a snowy wooden fence post, and a pair of shiny ice skates resting in the snow",
        "suggested_diffs": [
            "🎨 Color Swap: Change the sliding penguin's scarf from bright red to teal blue",
            "🧽 Erase: Remove the little red robin bird perched on the wooden post",
            "🔄 Flip: Flip the penguin pushing the sled horizontally",
            "📋 Clone: Duplicate a mug of hot cocoa on the bench"
        ]
    },
    {
        "title": "Woodland Forest Animals Decorating the Giant Pine Tree",
        "setting": "an enchanted snowy forest clearing framed by frosted pine boughs under a soft pastel winter sky",
        "characters": "a friendly brown bear cub, a fluffy red fox in a yellow knit sweater, a white snow bunny, and a tiny squirrel",
        "action": "working together to decorate a large outdoor evergreen Christmas tree with colorful baubles, gingerbread ornaments, and dried orange slices",
        "objects": "a woven wicker basket filled with shiny Christmas ornaments, a golden star tree-topper, strings of cranberry garland, a glowing snow lantern, and a small wooden ladder",
        "suggested_diffs": [
            "🎨 Color Swap: Change the fox's sweater from warm yellow to bright purple",
            "🧽 Erase: Remove the squirrel perched on the lower tree branch",
            "🔄 Flip: Flip the snow bunny holding a bauble to face the opposite direction",
            "📋 Clone: Duplicate a red glass bauble on the Christmas tree"
        ]
    },
    {
        "title": "Cozy Living Room by the Fireplace on Christmas Morning",
        "setting": "a warm, rustic country living room with a stone hearth fireplace crackling with gentle orange flames",
        "characters": "a sleepy golden retriever puppy sleeping peacefully on a fluffy red circular rug next to a curious kitten with a bell collar",
        "action": "resting in front of a grand decorated Christmas tree overflowing with colorful lights, tinsel, and wrapped gifts",
        "objects": "four colorful patterned stockings hanging from the mantelpiece, a plate of frosted sugar cookies and glass of milk, five distinctly colored gift boxes, and a grandfather clock",
        "suggested_diffs": [
            "🎨 Color Swap: Change the kitten's collar from red to emerald green",
            "🧽 Erase: Remove the second stocking hanging from the fireplace mantel",
            "🔄 Flip: Flip the sleeping puppy's body horizontally",
            "📋 Clone: Duplicate one of the striped gift boxes under the tree"
        ]
    },
    {
        "title": "Gingerbread House Bakery with Mouse Pastry Chefs",
        "setting": "a whimsical miniature bakery kitchen set inside a giant frosted gingerbread cottage",
        "characters": "three cute tiny field mice wearing tall white baker chef hats and red striped aprons",
        "action": "piping white royal icing onto gingerbread men, placing red and green gumdrops on the roof, and rolling out sugar cookie dough",
        "objects": "giant striped candy canes, a glass jar filled with rainbow gumdrops, a wooden rolling pin, a silver bowl of chocolate chips, a tray of star cookies, and a marshmallow chimney",
        "suggested_diffs": [
            "🎨 Color Swap: Change the gumdrop color on the gingerbread roof from red to sapphire blue",
            "🧽 Erase: Remove the wooden rolling pin resting on the flour-dusted table",
            "🔄 Flip: Flip the mouse holding the icing piping bag horizontally",
            "📋 Clone: Duplicate a star cookie on the metal baking tray"
        ]
    },
    {
        "title": "Polar Bear Cubs Building a Snow Fort & Sledding",
        "setting": "a sunny snow-covered arctic hill overlooking distant pastel blue icebergs and glowing pine trees",
        "characters": "three playful fluffy polar bear cubs wearing colorful knitted beanies and thick wool mittens",
        "action": "building a snow fortress with snow brick molds, tossing gentle snowballs, and sliding down a wooden toboggan",
        "objects": "a stack of five round snowballs, a bright red wooden sled, a blue snow shovel stuck in the snowbank, a wooden target board with painted bullseye, and a bucket of pinecones",
        "suggested_diffs": [
            "🎨 Color Swap: Change the wooden sled color from bright red to sunny yellow",
            "🧽 Erase: Remove the blue snow shovel stuck in the snowbank",
            "🔄 Flip: Flip the cub sitting on the sled to face backwards",
            "📋 Clone: Duplicate one of the snowballs on the snow fort wall"
        ]
    },
    {
        "title": "Outdoor Winter Hot Chocolate & Marshmallow Stand",
        "setting": "a charming outdoor holiday market wooden booth decorated with festive pine garlands and fairy lights",
        "characters": "a smiling friendly snowman vendor with a carrot nose and top hat serving cocoa to two happy woodland bunnies",
        "action": "pouring rich hot chocolate from a copper kettle into festive ceramic mugs topped with giant fluffy marshmallows",
        "objects": "a blackboard menu sign showing festive drawings, large glass jars filled with mini marshmallows and peppermint sticks, a pile of firewood logs, and a hanging brass bell",
        "suggested_diffs": [
            "🎨 Color Swap: Change the snowman's top hat ribbon from red to royal purple",
            "🧽 Erase: Remove the hanging brass bell on the roof corner of the booth",
            "🔄 Flip: Flip one of the bunnies drinking cocoa horizontally",
            "📋 Clone: Duplicate a jar of peppermint sticks on the wooden counter"
        ]
    },
    {
        "title": "Santa's Reindeer Barn & Holiday Sleigh Prep",
        "setting": "a warm wooden barn with golden straw on the floor, mistletoe hanging from timber beams, and snow gently falling outside the open door",
        "characters": "two friendly brown reindeer with velvety antlers wearing leather harnesses with shiny golden jingle bells, and an elf helper",
        "action": "munching on fresh orange carrots from a wooden trough while an elf polishes the runners of Santa's ornate red sleigh",
        "objects": "Santa's grand red and gold sleigh, a wooden bucket full of orange carrots, a lantern glowing on an iron wall hook, a bag of reindeer magic oats, and a decorated evergreen wreath",
        "suggested_diffs": [
            "🎨 Color Swap: Change the harness ribbon on the reindeer from red to cyan blue",
            "🧽 Erase: Remove the glowing lantern hanging on the wall hook",
            "🔄 Flip: Flip the elf holding the polishing cloth horizontally",
            "📋 Clone: Duplicate a carrot sticking out of the wooden bucket"
        ]
    },
    {
        "title": "Winter Village Square Christmas Market",
        "setting": "a lively cobblestone village square covered in soft snow, flanked by colorful Bavarian cottages with snow-covered gables",
        "characters": "cheerful village children and cute dogs in holiday sweaters strolling through the festive market stalls",
        "action": "window shopping at toy stalls, drinking hot apple cider, and admiring the enormous central community Christmas tree",
        "objects": "a vintage black street lamppost wrapped in red ribbon, a wooden vendor cart with handmade wooden nutcrackers, a pile of festive wreaths, a fire pit, and hanging pennant banners",
        "suggested_diffs": [
            "🎨 Color Swap: Change the red ribbon on the street lamppost to golden yellow",
            "🧽 Erase: Remove the nutcracker standing on the left side of the cart",
            "🔄 Flip: Flip the little dog in the sweater horizontally",
            "📋 Clone: Duplicate a hanging pennant flag along the market roof"
        ]
    },
    {
        "title": "North Pole Post Office Mail Sorting Room",
        "setting": "a bustling vintage holiday mailroom filled with wooden pigeonholes, brass scales, and stacks of colorful envelopes",
        "characters": "two diligent elf postal workers wearing green mail satchels and round spectacles",
        "action": "stamping letters with wax seals, sorting colorful letters addressed to Santa, and packing burlap mailbags",
        "objects": "a giant brass letter scale, a tall stack of letters tied with red twine, a wooden mail sorting desk with pigeonhole cubbies, ink pads (red and green), and mail sacks overflowing with letters",
        "suggested_diffs": [
            "🎨 Color Swap: Change the color of the top envelope in the stack from white to bright pink",
            "🧽 Erase: Remove the ink pad on the corner of the wooden desk",
            "🔄 Flip: Flip the elf stamping letters horizontally",
            "📋 Clone: Duplicate a mail sack resting on the floor"
        ]
    },
    {
        "title": "Children Building a Super Snowman in the Backyard",
        "setting": "a bright sunny backyard covered in thick virgin snow, with a wooden fence and snowy evergreen trees in the background",
        "characters": "a boy in a blue snowsuit and a girl in a pink winter jacket happily finishing an elaborate, jolly snowman",
        "action": "inserting a long orange carrot nose, button eyes, and wrapping a long striped scarf around the snowman's neck",
        "objects": "the jolly snowman with a black bowler hat and branch arms, a red plastic snow shovel, a wooden box of charcoal buttons, a watering can, and a little bluebird perched on the fence",
        "suggested_diffs": [
            "🎨 Color Swap: Change the snowman's striped scarf from red/white to green/white",
            "🧽 Erase: Remove the bluebird sitting on the wooden fence",
            "🔄 Flip: Flip the girl placing the button horizontally",
            "📋 Clone: Duplicate a coal button on the snowman's belly"
        ]
    },
    {
        "title": "Snowy Owl Family in a Frosted Pine Hollow",
        "setting": "a peaceful winter forest hollow inside an ancient hollow oak tree covered in sparkling icicles and snow clumps",
        "characters": "a wise fluffy white mother snowy owl and two adorable baby owlets with big yellow curious eyes",
        "action": "perched cozily on a dry branch lined with soft pine needles, watching fluffy snowflakes drift down from the evening sky",
        "objects": "clusters of bright red winter holly berries, glowing icicles hanging from the hollow opening, a pinecone resting on the bark ledge, and a starry crescent moon in the twilight background",
        "suggested_diffs": [
            "🎨 Color Swap: Change the holly berries from crimson red to golden yellow",
            "🧽 Erase: Remove the pinecone resting on the hollow ledge",
            "🔄 Flip: Flip the baby owlet on the right side horizontally",
            "📋 Clone: Duplicate an icicle hanging from the hollow roof"
        ]
    },
    {
        "title": "Holiday Polar Express Toy Train at a Snowy Depot",
        "setting": "a charming miniature train station platform surrounded by snowbanks, wooden fences, and decorated streetlamps",
        "characters": "a friendly badger conductor in a blue uniform holding a pocket watch, and a family of mice passengers with tiny suitcases",
        "action": "welcoming passengers aboard a colorful red and green holiday steam train puffing fluffy white steam",
        "objects": "the steam train locomotive with a wreath on the front cowcatcher, a station clock showing 12:00, small vintage leather suitcases, a brass bell, and a wooden bench with holiday gifts",
        "suggested_diffs": [
            "🎨 Color Swap: Change the conductor's tie from gold to bright red",
            "🧽 Erase: Remove the wreath on the front of the train locomotive",
            "🔄 Flip: Flip the badger conductor holding the pocket watch horizontally",
            "📋 Clone: Duplicate a vintage suitcase on the wooden platform"
        ]
    },
    {
        "title": "Squirrel and Hedgehog Winter Tea Party",
        "setting": "a warm underground burrow home underneath tree roots, illuminated by glowing mushroom lamps and a tiny clay woodstove",
        "characters": "a cheerful squirrel in a wool vest and a gentle hedgehog wrapped in a colorful patchwork blanket",
        "action": "sitting across a small tree-slice table, sipping acorn tea from ceramic cups and sharing baked apple slices",
        "objects": "a steaming ceramic teapot with floral patterns, a basket of dried hazelnuts and acorns, a tiny bookcase filled with miniature books, a knitted rug, and a kettle on the woodstove",
        "suggested_diffs": [
            "🎨 Color Swap: Change the ceramic teapot color from sky blue to soft lavender",
            "🧽 Erase: Remove the tiny book resting on the side table",
            "🔄 Flip: Flip the hedgehog holding the teacup horizontally",
            "📋 Clone: Duplicate an acorn on the wooden table"
        ]
    },
    {
        "title": "Arctic Ice Castle Courtyard with Friendly Yetis",
        "setting": "a fantastical ice palace courtyard carved out of translucent turquoise glacier ice with glittering ice chandeliers",
        "characters": "two friendly, fluffy white yeti creatures with blue horns and cute smiles, wearing holiday flower garlands",
        "action": "carving playful animal ice sculptures and stringing colorful crystalline lanterns between ice pillars",
        "objects": "an ice sculpture of a dolphin, ice chisels and wooden mallets on a pedestal, colorful floating crystal lanterns, a grand ice throne with purple velvet cushion, and snow pedestals",
        "suggested_diffs": [
            "🎨 Color Swap: Change the velvet cushion on the ice throne from purple to crimson red",
            "🧽 Erase: Remove the ice chisel tool on the pedestal",
            "🔄 Flip: Flip the yeti holding the crystal lantern horizontally",
            "📋 Clone: Duplicate a floating crystal lantern near the ice pillar"
        ]
    },
    {
        "title": "Christmas Tree Farm with Vintage Red Tractor",
        "setting": "a scenic hillside tree farm covered in fresh snow with rows of neat symmetrical pine and spruce trees",
        "characters": "a golden lab dog wearing a reindeer antler headband trotting happily next to a child carrying a small freshly cut fir tree",
        "action": "loading Christmas trees onto the wooden trailer of a charming vintage tractor",
        "objects": "a vintage red farm tractor with big black tires, a wooden trailer piled with green trees tied in jute twine, a 'Fresh Cut Trees' painted wooden sign, a red thermos, and a hand saw",
        "suggested_diffs": [
            "🎨 Color Swap: Change the vintage tractor color from red to emerald green",
            "🧽 Erase: Remove the hand saw resting on the tractor trailer",
            "🔄 Flip: Flip the golden lab dog wearing the antlers horizontally",
            "📋 Clone: Duplicate a cut pine tree loaded on the trailer"
        ]
    },
    {
        "title": "Santa's Sleigh on a Snowy Village Rooftop at Midnight",
        "setting": "a picturesque snowy rooftop with brick chimneys overlooking a quiet slumbering village under a starry Christmas Eve sky with a full moon",
        "characters": "Santa Claus in his traditional crimson suit with white fur trim and a white beard, checking his pocket watch",
        "action": "quietly stepping out of his grand sleigh towards a cobblestone chimney with a giant sack of toys over his shoulder",
        "objects": "Santa's ornate sleigh loaded with wrapped presents, a giant velvet toy sack, a brick chimney capped in snow, a weather vane shaped like a rooster, and a bright North Star shining in the sky",
        "suggested_diffs": [
            "🎨 Color Swap: Change the rooster weather vane color from black iron to polished copper gold",
            "🧽 Erase: Remove the small present perched on the back edge of the sleigh",
            "🔄 Flip: Flip Santa stepping towards the chimney horizontally",
            "📋 Clone: Duplicate one of the stars twinkling in the clear night sky"
        ]
    },
    {
        "title": "Festive Holiday Greenhouse & Winter Botanical Garden",
        "setting": "a grand Victorian glass greenhouse filled with vibrant red poinsettia flowers, frosted glass panes, and hanging brass lanterns",
        "characters": "two friendly gardener elves wearing denim overalls and striped woolen beanies",
        "action": "watering lush potted poinsettias, trimming evergreen boughs for wreaths, and potting amaryllis bulbs in clay pots",
        "objects": "rows of vibrant red poinsettia pots on wooden tables, a vintage brass watering can, hanging mistletoe balls, a stack of terracotta flowerpots, and a small wheelbarrow with soil",
        "suggested_diffs": [
            "🎨 Color Swap: Change one of the poinsettia flower clusters from bright red to pure white",
            "🧽 Erase: Remove the brass watering can on the table",
            "🔄 Flip: Flip the elf potting the plant horizontally",
            "📋 Clone: Duplicate a terracotta pot on the ground"
        ]
    },
    {
        "title": "Cozy Mountain Ski Chalet Porch with Steaming Mugs",
        "setting": "a covered wooden porch of a rustic Swiss-style alpine chalet with icicles hanging from the roof and panoramic mountain peaks",
        "characters": "a cute Saint Bernard dog with a traditional wooden barrel collar resting next to a pair of kids in colorful winter ski gear",
        "action": "relaxing on wooden Adirondack chairs after skiing, enjoying roasted marshmallows on sticks over a fire bowl",
        "objects": "two pairs of colorful skis and ski poles leaning against the log wall, snowshoes hanging on a peg, steaming mugs of hot cider, knitted wool blankets, and a basket of firewood",
        "suggested_diffs": [
            "🎨 Color Swap: Change the ski jacket color from neon orange to royal blue",
            "🧽 Erase: Remove the snowshoes hanging on the wall peg",
            "🔄 Flip: Flip the Saint Bernard dog lying on the porch rug horizontally",
            "📋 Clone: Duplicate a roasting marshmallow stick by the fire bowl"
        ]
    },
    {
        "title": "Baby Deer (Fawn) Experiencing First Snowfall",
        "setting": "a gentle birch tree forest with peeling white bark and soft powdery snow falling silently from a lilac twilight sky",
        "characters": "a curious spotted baby fawn with big brown eyes, a fluffy snow bunny, and a tiny red cardinal bird",
        "action": "gently sniffing a snowflake resting on a fallen pinecone, surrounded by peaceful woodland tranquility",
        "objects": "fallen birch logs with green moss and snow caps, clusters of red winterberries, a snow-covered boulder, animal pawprints in the snow, and frosted wild ferns",
        "suggested_diffs": [
            "🎨 Color Swap: Change the red cardinal bird into a bright yellow finch",
            "🧽 Erase: Remove the pinecone on the fallen log",
            "🔄 Flip: Flip the snow bunny to look in the opposite direction",
            "📋 Clone: Duplicate a cluster of winterberries on the bush"
        ]
    }
]

# Variations and modifiers to generate infinite unique combinations
LIGHTING_MOODS = [
    "crisp bright sunny winter morning lighting with sparkling snow reflections",
    "cozy golden afternoon sunlight casting warm shadows across the snow",
    "magical twilight hour with warm glowing lanterns and pastel lilac sky",
    "soft diffused snowy daylight with gentle fluffy snowflakes drifting down",
    "cheerful festive evening ambiance with glowing fairy lights and stars"
]

COLOR_PALETTES = [
    "classic vibrant Christmas palette of rich cherry red, emerald pine green, warm gold, and crisp white snow",
    "cozy winter pastel palette of baby blue, mint green, soft blush pink, and frosted silver accents",
    "warm Scandinavian holiday palette of deep berry red, navy blue, gingerbread tan, and snow white",
    "playful vibrant cartoon colors with high saturation, rich jewel tones, and clean color separation"
]

EXTRA_ACCENTS = [
    "decorated with festive red satin ribbons and silver jingle bells",
    "surrounded by tiny friendly forest birds and sparkling snow sparkles",
    "with strings of colorful holiday fairy lights glowing warmly across the scene",
    "with whimsical candy canes, peppermint swirls, and pine boughs accenting the borders",
    "with cozy knitted textures on scarves and beanies with fluffy white pom-poms"
]

# ---------------------------------------------------------------------------
# 2. OTHER NICHES (FOR EXPANSION)
# ---------------------------------------------------------------------------

OTHER_NICHES = {
    "cute_animals": {
        "name": "Cute Animals & Pets for Kids",
        "foundations": [
            {
                "title": "Sunny Farmyard Playground",
                "setting": "a cheerful sunny red farmyard with a green grassy meadow and wooden fences",
                "characters": "a friendly spotted cow, a fluffy pink piglet playing in clean mud, and three yellow baby chicks",
                "action": "playing around a wooden water trough and eating crunchy red apples under an apple tree",
                "objects": "red wooden barn, blue tractor in background, metal milk pail, woven basket of red apples, sunflowers along the fence",
                "suggested_diffs": ["Color Swap: Change the tractor from blue to green", "Erase: Remove one baby chick", "Flip: Flip the cow horizontally", "Clone: Duplicate an apple in the basket"]
            },
            {
                "title": "Jungle Animal Picnic by the Waterfall",
                "setting": "a lush vibrant tropical jungle with a sparkling turquoise waterfall and giant green monstera leaves",
                "characters": "a baby elephant spraying water, a cheerful monkey hanging from a vine, and a colorful toucan",
                "action": "sharing tropical fruits like bananas, pineapples, and watermelons on a large flat river rock",
                "objects": "wooden picnic basket, bunch of yellow bananas, floating water lilies, purple exotic orchids, coconut with straw",
                "suggested_diffs": ["Color Swap: Change the toucan's beak color from orange to blue", "Erase: Remove the coconut drink", "Flip: Flip the monkey hanging on the vine", "Clone: Duplicate a water lily in the river"]
            }
        ]
    },
    "fairy_tale": {
        "name": "Fairy Tale & Fantasy Castles",
        "foundations": [
            {
                "title": "Friendly Dragon's Castle Courtyard",
                "setting": "a magical stone castle courtyard with purple slate roofs, golden spires, and blooming rose gardens",
                "characters": "a cute, chubby green baby dragon wearing a tiny golden crown and a smiling princess in a pink gown",
                "action": "roasting marshmallows with the baby dragon's gentle little smoke puffs while a friendly cat watches",
                "objects": "stone fountain with carved gargoyle, heraldic shield with lion crest, wooden treasure chest with gems, royal banner",
                "suggested_diffs": ["Color Swap: Change the princess gown from pink to royal blue", "Erase: Remove the heraldic shield on the wall", "Flip: Flip the baby dragon horizontally", "Clone: Duplicate a gem on the treasure chest"]
            }
        ]
    },
    "space_adventure": {
        "name": "Space & Astronaut Animals",
        "foundations": [
            {
                "title": "Moon Base Astronaut Animals Exploration",
                "setting": "a colorful cartoon lunar surface with crater pools, friendly glowing alien flowers, and a view of planet Earth",
                "characters": "a brave puppy astronaut in a white spacesuit with glass dome helmet, and a friendly friendly three-eyed green alien",
                "action": "planting a colorful flag and collecting glowing lunar space crystals in a research rover",
                "objects": "lunar rover vehicle with radar dish, space flag with rocket emblem, glowing purple space rocks, crater with bubble pool",
                "suggested_diffs": ["Color Swap: Change the space flag from red to yellow", "Erase: Remove the radar dish on the rover", "Flip: Flip the alien waving horizontally", "Clone: Duplicate a glowing space rock"]
            }
        ]
    }
}

# ---------------------------------------------------------------------------
# 3. PROMPT GENERATOR CORE LOGIC
# ---------------------------------------------------------------------------

def generate_prompts(
    niche: str = "winter_christmas",
    count: int = 50,
    target_model: str = "midjourney",
    aspect_ratio: str = "1:1"
) -> List[Dict[str, Any]]:
    """
    Generates `count` unique prompts tailored specifically for spot-the-difference activity books.
    """
    results = []

    # Choose pool
    if niche == "winter_christmas" or niche not in OTHER_NICHES:
        pool = WINTER_CHRISTMAS_FOUNDATIONS
        niche_label = "Winter & Christmas for Kids"
    else:
        pool = OTHER_NICHES[niche]["foundations"]
        niche_label = OTHER_NICHES[niche]["name"]

    # If count > pool size, cycle and dynamically augment each with unique variations
    for i in range(count):
        base_item = pool[i % len(pool)]
        cycle_idx = i // len(pool)

        # Dynamic variation elements
        lighting = LIGHTING_MOODS[(i * 3 + cycle_idx) % len(LIGHTING_MOODS)]
        palette = COLOR_PALETTES[(i * 2 + cycle_idx) % len(COLOR_PALETTES)]
        accent = EXTRA_ACCENTS[(i * 5 + cycle_idx) % len(EXTRA_ACCENTS)]

        # Unique variant title
        var_num = f" (Scene {i + 1})" if count > len(pool) else ""
        title = f"{base_item['title']}{var_num}"

        # Build prompt base
        prompt_parts = [
            f"Children's picture book illustration of {base_item['characters']}",
            f"{base_item['action']}",
            f"{base_item['setting']}",
            f"Key distinct objects in scene: {base_item['objects']}",
            f"{lighting}",
            f"{palette}",
            f"{accent}",
            "Style: clean vector cartoon art style with bold distinct outlines, flat saturated color separation, high visual contrast between objects, perfectly isolated recognizable items, spot the difference puzzle illustration, whimsical storybook aesthetic, highly detailed, clean crisp edges, zero text, no watermarks, no blur, no noise"
        ]

        full_prompt_text = ", ".join(prompt_parts)

        # Format according to target AI model
        if target_model == "midjourney":
            # Midjourney v6 parameters
            ar_param = f"--ar {aspect_ratio}" if aspect_ratio else "--ar 1:1"
            formatted_prompt = f"/imagine prompt: {full_prompt_text} {ar_param} --v 6.1 --style raw"
        elif target_model == "dalle":
            # DALL-E 3: Needs paragraph format without flags
            ar_desc = "Square aspect ratio (1:1), high resolution 300 DPI print quality." if aspect_ratio == "1:1" else "Portrait orientation (3:4 aspect ratio)."
            formatted_prompt = f"{full_prompt_text}. {ar_desc}"
        elif target_model == "flux":
            # Flux 1.0 format
            formatted_prompt = f"{full_prompt_text}, 8k resolution, ultra-clean vector lines, masterpiece, vibrant children book art"
        else:  # Universal
            formatted_prompt = full_prompt_text

        # Create copy of suggested differences with dynamic adjustments
        diffs = list(base_item["suggested_diffs"])

        results.append({
            "id": i + 1,
            "title": title,
            "prompt": formatted_prompt,
            "raw_text": full_prompt_text,
            "suggested_differences": diffs,
            "target_model": target_model,
            "aspect_ratio": aspect_ratio,
            "niche": niche_label
        })

    return results

def get_available_niches() -> List[Dict[str, str]]:
    """Returns list of selectable niches for UI."""
    return [
        {"id": "winter_christmas", "name": "❄️ Winter & Christmas for Kids (⭐ Recommended)", "count": len(WINTER_CHRISTMAS_FOUNDATIONS)},
        {"id": "cute_animals", "name": "🐾 Cute Farm & Jungle Animals", "count": len(OTHER_NICHES["cute_animals"]["foundations"])},
        {"id": "fairy_tale", "name": "🏰 Fairy Tale & Magic Castles", "count": len(OTHER_NICHES["fairy_tale"]["foundations"])},
        {"id": "space_adventure", "name": "🚀 Astronaut Animals & Space Exploration", "count": len(OTHER_NICHES["space_adventure"]["foundations"])}
    ]

if __name__ == "__main__":
    # Test generation of 50 prompts
    test_prompts = generate_prompts(niche="winter_christmas", count=50, target_model="midjourney", aspect_ratio="1:1")
    print(f"Successfully generated {len(test_prompts)} prompts!")
    print("\n--- SAMPLE PROMPT #1 ---")
    print("Title:", test_prompts[0]["title"])
    print("Prompt:", test_prompts[0]["prompt"][:180] + "...")
    print("Diff count:", len(test_prompts[0]["suggested_differences"]))
