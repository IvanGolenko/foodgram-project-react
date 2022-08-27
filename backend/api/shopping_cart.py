import io

from django.http import FileResponse
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from rest_framework.views import APIView

from recipes.models import IngredientInRecipe


class DownloadCartView(APIView):

    def get(self, request):
        user = request.user
        shopping_cart = user.purchases.all()
        buying_list = {}
        for record in shopping_cart:
            recipe = record.recipe
            ingredients = IngredientInRecipe.objects.filter(recipe=recipe)
            for ingredient in ingredients:
                amount = ingredient.amount
                name = ingredient.ingredient.name
                measurement_unit = ingredient.ingredient.measurement_unit
                if name not in buying_list:
                    buying_list[name] = {
                        'measurement_unit': measurement_unit,
                        'amount': amount
                    }
                else:
                    buying_list[name]['amount'] = (buying_list[name]['amount']
                                                   + amount)
        shoping_list = []
        shoping_list.append('Список покупок:')
        for item in buying_list:
            shoping_list.append(f'{item} - {buying_list[item]["amount"]} '
                                f'{buying_list[item]["measurement_unit"]}')
        shoping_list.append(' ')
        shoping_list.append('FoodGram, 2022')
        pdfmetrics.registerFont(TTFont('DejaVuSerif',
                                       './api/ttf/DejaVuSerif.ttf'))
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer)
        p.setFont("DejaVuSerif", 15)
        start = 800
        for line in shoping_list:
            p.drawString(50, start, line)
            start -= 20
        p.showPage()
        p.save()
        buffer.seek(0)
        return FileResponse(buffer, as_attachment=True,
                            filename='cart_list.pdf')
