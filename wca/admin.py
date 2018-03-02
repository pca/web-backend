from django.contrib import admin

from wca.models import (
    Competition, Continent, Country, Event,
    Format, Person, RanksAverage, RanksSingle,
    Result, RoundTypes, Scramble,
)

admin.site.register(Competition)
admin.site.register(Continent)
admin.site.register(Country)
admin.site.register(Event)
admin.site.register(Format)
admin.site.register(Person)
admin.site.register(RanksAverage)
admin.site.register(RanksSingle)
admin.site.register(Result)
admin.site.register(RoundTypes)
admin.site.register(Scramble)
