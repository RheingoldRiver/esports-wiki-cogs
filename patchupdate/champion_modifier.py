import re

from patchupdate.template_modifier import TemplateModifier


def capfirst(s):
    """Capitalize the very first character of a string"""
    return re.sub(r'^.', lambda m: m.group().upper(), s)


class ChampionModifier(TemplateModifier):
    def format_template(self, ddid):
        data = self.data['data']

        self.put('name', data[ddid]['name'])
        self.put('title', capfirst(data[ddid]['title']))

        self.put('key_int', data[ddid]['key'])

        self.put('resource', data[ddid]['partype'])
        self.put('attribute', data[ddid]['tags'][0])
        self.put('attribute2', data[ddid]['tags'][1] if len(data[ddid]['tags']) > 1 else '')

        self.put('hp', data[ddid]['stats']['hp'])
        self.put('hp_lvl', data[ddid]['stats']['hpperlevel'])
        self.put('hpregen', data[ddid]['stats']['hpregen'])
        self.put('hpregen_lvl', data[ddid]['stats']['hpregenperlevel'])
        self.put('mana', data[ddid]['stats']['mp'] if data[ddid]['partype'] == 'Mana' else '')
        self.put('mana_lvl', data[ddid]['stats']['mpperlevel'] if data[ddid]['partype'] == 'Mana' else '')
        self.put('mregen', data[ddid]['stats']['mpregen'] if data[ddid]['partype'] == 'Mana' else '')
        self.put('mregen_lvl', data[ddid]['stats']['mpregenperlevel'] if data[ddid]['partype'] == 'Mana' else '')
        self.put('range', data[ddid]['stats']['attackrange'])
        self.put('ad', data[ddid]['stats']['attackdamage'])
        self.put('ad_lvl', data[ddid]['stats']['attackdamageperlevel'])
        self.put('as', data[ddid]['stats']['attackspeed'])
        self.put('as_lvl', data[ddid]['stats']['attackspeedperlevel'])
        self.put('armor', data[ddid]['stats']['armor'])
        self.put('armor_lvl', data[ddid]['stats']['armorperlevel'])
        self.put('mr', data[ddid]['stats']['spellblock'])
        self.put('mr_lvl', data[ddid]['stats']['spellblockperlevel'])
        self.put('ms', data[ddid]['stats']['movespeed'])
