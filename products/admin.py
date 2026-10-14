from django.contrib import admin
from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'unit', 'in_stock', 'stock_quantity')
    list_filter = ('category', 'in_stock', 'is_organic')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
