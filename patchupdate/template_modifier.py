from mwcleric.template_modifier import TemplateModifierBase


class TemplateModifier(TemplateModifierBase):
    def update_template(self, template):
        key = [k for k, v in self.data['data'].items()
               if v.get('name') == self.current_template.get('name', '').value.strip()]
        if len(key) == 1:
            ddid = key[0]
            self.current_template.add('ddragon_key', ddid)
        else:
            self.site.log_error_content(self.current_page.name, "Duplicate or missing DDragon data")
            return

        self.format_template(ddid)

    def format_template(self, ddid):
        raise NotImplementedError()

    def put(self, key, value):
        if str(value):
            self.current_template.add(key, str(value))
        else:
            if self.current_template.has(key) and not self.current_template.get(key).value.strip():
                self.current_template.remove(key, True)
