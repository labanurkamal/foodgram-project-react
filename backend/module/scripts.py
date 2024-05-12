from collections import defaultdict


def combine_ingredients(ingredients_list):
    """Комбинирование ингредиентов."""
    totals = defaultdict(int)
    for item in ingredients_list:
        totals[(item['name'], item['measurement_unit'])] += item['amount']
    return [
        {'name': name, 'measurement_unit': unit, 'amount': amount}
        for (name, unit), amount in totals.items()
    ]


def txt_export(combine_ingredients):
    """Экспорт списка ингредиентов в текстовый файл."""
    dict_unit = {'кг': (1000, 'г'), 'л': (1000, 'мл')}
    title = 'Название | Единица измерения | Количество'
    line_len, filename = '-' * len(title), 'list_shopping_cart-export.txt'

    with open(filename, 'w', encoding='utf-8') as file:
        file.write(f'{title}\n{line_len}\n')
        for i, item in enumerate(combine_ingredients, start=1):
            amount, measurement_unit = item['amount'], item['measurement_unit']
            m_unit = dict_unit.get(measurement_unit)
            if m_unit:
                measurement_unit = m_unit[1]
                amount *= m_unit[0]
            file.write((f'{i}. {item["name"]} ({measurement_unit})'
                        f' — {amount}\n'))
        file.write(f'{line_len}')

    return filename
