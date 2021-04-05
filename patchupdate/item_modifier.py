from patchupdate.template_modifier import TemplateModifier


def strperc(i):
    """Nicely turn a decimal into a percent"""
    if not i:
        return ''
    elif float(i * 100) % 1 == 0:
        return str(int(float(i) * 100)) + '%'
    else:
        return str(float(i * 100)) + '%'


class ItemModifier(TemplateModifier):
    def format_template(self, ddid):
        data = self.data['data']

        self.put('name', data[ddid]['name'])
        self.put('item_code', None)

        self.put('ad', data[ddid]['stats'].get('FlatPhysicalDamageMod', ''))
        self.put('ls', strperc(data[ddid]['stats'].get('PercentLifeStealMod', '')))
        self.put('hp', data[ddid]['stats'].get('FlatHPPoolMod', ''))
        self.put('hpregen', data[ddid]['stats'].get('FlatHPRegenMod', ''))
        self.put('armor', data[ddid]['stats'].get('FlatArmorMod', ''))
        self.put('mr', data[ddid]['stats'].get('FlatSpellBlockMod', ''))
        self.put('crit', data[ddid]['stats'].get('FlatCritChanceMod', ''))
        self.put('as', strperc(data[ddid]['stats'].get('PercentAttackSpeedMod', '')))
        self.put('totalgold', data[ddid]['gold']['total'])
        self.put('sold', data[ddid]['gold']['sell'])

        items = []
        for item_id in data[ddid]['into']:
            items.append(data[item_id]['name'])
        self.put('used_in', ','.join(items))
