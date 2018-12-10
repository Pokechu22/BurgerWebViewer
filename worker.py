import sys
# HACK: Paths from main script aren't copied.  Transfer via sys.argv
new_path = [loc for loc in sys.argv if loc not in sys.path]
sys.path.extend(new_path)

import json
import traceback
from html import escape
from browser.webworker import current_worker, Message

def progress_update(text, value=None, max=None):
    data = {'desc': text}
    if value is not None and max is not None:
        data['value'] = value
        data['max'] = max

    current_worker.post_message(Message('progress', data))


def hamburglar(main, diff):
    progress_update('Hamburglar: Importing hamburglar')
    import hamburglar_main

    def import_toppings():
        # Silly hardcoded thing; we can't go through all files here
        from hamburglar.toppings.achivements import AchivementsTopping
        from hamburglar.toppings.packets import PacketsTopping
        from hamburglar.toppings.recipes import RecipesTopping
        from hamburglar.toppings.stats import StatsTopping
        from hamburglar.toppings.tags import TagsTopping
        from hamburglar.toppings.version import VersionTopping
        from hamburglar.toppings.biomes import BiomesTopping
        from hamburglar.toppings.blocks import BlocksTopping
        from hamburglar.toppings.entities import EntitiesTopping
        from hamburglar.toppings.entities import ObjectsTopping
        from hamburglar.toppings.items import ItemsTopping
        from hamburglar.toppings.sounds import SoundsTopping
        from hamburglar.toppings.tileentities import TileEntitiesTopping
        from hamburglar.toppings.language import LanguageTopping

        return (AchivementsTopping, PacketsTopping, RecipesTopping, StatsTopping, TagsTopping, VersionTopping, BiomesTopping, BlocksTopping, EntitiesTopping, ObjectsTopping, ItemsTopping, SoundsTopping, TileEntitiesTopping, LanguageTopping)

    progress_update('Hamburglar: Importing toppings')
    toppings = import_toppings()

    num_updates = 0
    def progress_callback(name):
        nonlocal num_updates
        progress_update("Hamburglar: " + name, num_updates, len(toppings))
        num_updates += 1

    return hamburglar_main.compare(toppings, main[0], diff[0], progress_callback=progress_callback)

def vitrine(data, all_data):
    progress_update('Vitrine: Importing vitrine')
    import vitrine_main

    def import_toppings():
        # Silly hardcoded thing
        from vitrine.toppings.achievements import AchievementsTopping
        from vitrine.toppings.biomes import BiomesTopping
        from vitrine.toppings.entities import EntitiesTopping
        from vitrine.toppings.language import LanguageTopping
        from vitrine.toppings.objects import ObjectsTopping
        from vitrine.toppings.packets import PacketsTopping
        from vitrine.toppings.recipes import RecipesTopping
        from vitrine.toppings.sounds import SoundsTopping
        from vitrine.toppings.stats import StatsTopping
        from vitrine.toppings.tags import TagsTopping
        from vitrine.toppings.tileentities import TileEntities
        from vitrine.toppings.versions import VersionsTopping
        from vitrine.toppings.blocks import BlocksTopping
        from vitrine.toppings.items import ItemsTopping

        return (AchievementsTopping, BiomesTopping, EntitiesTopping, LanguageTopping, ObjectsTopping, PacketsTopping, RecipesTopping, SoundsTopping, StatsTopping, TagsTopping, TileEntities, VersionsTopping, BlocksTopping, ItemsTopping)

    progress_update('Vitrine: Importing toppings')
    toppings = import_toppings()

    num_updates = 0
    def progress_callback(name):
        nonlocal num_updates
        progress_update("Vitrine: " + name, num_updates, len(toppings))
        num_updates += 1

    return vitrine_main.generate_html(toppings, data, progress_callback=progress_callback)

def vitrine_worker(message_name, message, src):
    try:
        print("vitrine_worker:", message)
        data = message.data.to_dict()
        data = json.loads(data['data'])
        result = vitrine(data, data)
    except:
        traceback.print_exc()
        result = '<div class="entry"><h3>Error</h3><pre>' + escape(traceback.format_exc()) + '</pre></div>'
    print("Done!")
    current_worker.post_reply(message, Message('_vitrine', {"result": result}))

def hamburglar_worker(message_name, message, src):
    try:
        print("hamburglar_worker:", message)
        data = message.data.to_dict()
        main = json.loads(data['main'])
        diff = json.loads(data['diff'])
        combined = hamburglar(main, diff)
        print("Halfway done")
        result = vitrine(combined, {False: main, True: diff})
    except:
        print("!!!")
        traceback.print_exc()
        print("!!!")
        result = '<div class="entry"><h3>Error</h3><pre>' + escape(traceback.format_exc()) + '</pre></div>'
    print("Done")

    current_worker.post_reply(message, Message('_hamburglar', {"result": result}))

current_worker.bind_message('vitrine', vitrine_worker)
current_worker.bind_message('hamburglar', hamburglar_worker)
current_worker.exec()