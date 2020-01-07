import pandas as pd
import math

# Loads Recipes, defines conversion calculations
def RecipeLoad():
    global Recipes_Tools
    global Recipes_Ingredients
    global Recipes_Details
    global Conversions

    Recipes_Tools = pd.read_excel(r'C:\Users\franc\Documents\SousChef\Recipes.xlsx', sheet_name='Recipes (Tools)')
    Recipes_Ingredients = pd.read_excel(r'C:\Users\franc\Documents\SousChef\Recipes.xlsx', sheet_name='Recipes (Ingredients)')
    Recipes_Details = pd.read_excel(r'C:\Users\franc\Documents\SousChef\Recipes.xlsx', sheet_name='Recipes (Details)')
    Conversions = pd.read_excel(r'C:\Users\franc\Documents\SousChef\Recipes.xlsx', sheet_name='Conversion Table')

    # Merges all Recipe Units with Conversion Table to provide Metric conversion figures for single quantities
    x = Recipes_Ingredients.merge(Conversions, how="left", left_on='Units', right_on='Units')
    # Uses conversion figures to create measurements for items with quantity > 1
    x["Liters"] = x["Liters"].multiply(x["Quantity"])
    x["Grams"] = x["Grams"].multiply(x["Quantity"])
    # Create variable "Generic Type" to track what Units are being used for each item
    x["Generic Type"] = x["Units"]
    x.loc[~ pd.isna(x["Grams"]), "Generic Type"] = "Grams"
    x.loc[~ pd.isna(x["Liters"]), "Generic Type"] = "Liters"
    x["Items"] = 0
    # This is ugly, but it assigns Quantity of Items to the
    # Measurement Value when the item is not measured in Liters or Grams
    x.loc[pd.isna(x["Grams"]) & pd.isna(x["Liters"]), "Items"] = x.loc[pd.isna(x["Grams"]) & pd.isna(x["Liters"]), "Quantity"]
    # Converts missing values to 0
    x.loc[pd.isna(x["Liters"]), "Liters"] = 0
    x.loc[pd.isna(x["Grams"]), "Grams"] = 0
    # Create variable "Generic Amount" to track the quantity of the Generic Type units
    x["Generic Amount"] = x["Liters"] + x["Grams"] + x["Items"]
    # Drop columns no longer needed
    x = x.drop(columns=["Units", "Quantity"])
    # Final assignment of Recipes Ingredients output
    Recipes_Ingredients = x

def RecipeSearch(AllowanceP = 0.0, AllowanceI = 1):
    global Profile_Tools
    global Profile_Ingredients
    global Profile_Preferences
    global Conversions
    global Missing
    global Recipes_Ingredients

    Profile_Tools = pd.read_excel(r'C:\Users\franc\Documents\SousChef\Recipes.xlsx', sheet_name='Profile (Tools)')
    Profile_Ingredients = pd.read_excel(r'C:\Users\franc\Documents\SousChef\Recipes.xlsx', sheet_name='Profile (Ingredients)')
    Profile_Preferences = pd.read_excel(r'C:\Users\franc\Documents\SousChef\Recipes.xlsx', sheet_name='Profile (Preferences)')

    x = Profile_Ingredients.merge(Conversions, how="left", left_on='Units', right_on='Units')
    # Uses conversion figures to create measurements for items with quantity > 1
    x["Liters"] = x["Liters"].multiply(x["Quantity"])
    x["Grams"] = x["Grams"].multiply(x["Quantity"])
    # Create variable "Generic Type" to track what Units are being used for each item
    x["Generic Type"] = x["Units"]
    x.loc[~ pd.isna(x["Grams"]), "Generic Type"] = "Grams"
    x.loc[~ pd.isna(x["Liters"]), "Generic Type"] = "Liters"
    x["Items"] = 0
    # This is ugly, but it assigns Quantity of Items to the
    # Measurement Value when the item is not measured in Liters or Grams - Allows for greater variety of user defined items
    x.loc[(x["Units"] != "Liters") & (x["Units"] != "Grams"), "Items"] = x.loc[(x["Units"] != "Liters") & (x["Units"] != "Grams"), "Quantity"]
    # Converts missing values to 0
    x.loc[pd.isna(x["Liters"]), "Liters"] = 0
    x.loc[pd.isna(x["Grams"]), "Grams"] = 0
    # Create variable "Generic Amount" to track the quantity of the Generic Type units
    x["Generic Amount"] = x["Liters"] + x["Grams"] + x["Items"]
    # Drop columns no longer needed
    x = x.drop(columns=["Units", "Quantity"])
    # Combine amounts of like ingredients
    y = x.groupby("Ingredient")["Generic Amount"].sum()
    x = x.merge(y, how="inner", left_on='Ingredient', right_on='Ingredient')
    x["Generic Amount"] = x["Generic Amount_y"]
    # Drop columns no longer needed
    x = x.drop(columns=["Generic Amount_x", "Generic Amount_y", "Items"])
    # Final assignment of Profile Ingredients output - Note the retention of unique rows only
    Profile_Ingredients = x.drop_duplicates(keep='last')

    # Search Algorithm
    # Find like ingredients between User and Recipe Database
    x = Profile_Ingredients.merge(Recipes_Ingredients, how="right", left_on ='Ingredient', right_on='Ingredient')
    # Initialize Test for the presence and amount of like ingredients
    x["Test"] = 0
    # Pass Test if amount is equal or greater than line items in the ingredients
    x.loc[x["Generic Amount_x"] >= x["Generic Amount_y"], "Test"] = 1
    # Creates new variables for the difference between the User and the Recipe Database
    x["Difference"] = x["Generic Amount_y"] - x["Generic Amount_x"]
    # Drop columns no longer needed
    x = x.drop(columns=["Liters_x",
                        "Grams_x",
                        "Generic Amount_x",
                        "Generic Type_x",
                        "Liters_y",
                        "Grams_y",
                        "Items"])
    #Rename Columns
    x.rename(columns = {"Generic Type_y":"Generic Type",
                        "Generic Amount_y":"Generic Amount"},
                        inplace = True)
    # Final assignment of Search Algorithm output
    Recipes_Ingredients = x

    # Test percentage of Recipe Line items User has for each recipe
    y = pd.DataFrame(Recipes_Ingredients.groupby("Recipe ID")["Test"].mean()).reset_index()
    y.rename(columns = {"Test":"Percentage"}, inplace=True)
    # Add recipe information (Name, URL, etc...)
    y = y.merge(Recipes_Details, how="inner", left_on ="Recipe ID", right_on ="Recipe ID")
    # Sort by Percentage to complete ingredients
    y = y.sort_values(by=["Type", "Percentage"], ascending=False)
    # Remove "Type" column as it is currently not utilized
    y = y.drop(columns=["Type"])
    # Remove duplicate entries
    y = y.drop_duplicates(keep='last')
    # Subset Recipes to where Percentage quota is met
    y = y.loc[y["Percentage"] >= AllowanceP]
    # Find items that are missing in order to complete all Recipes
    Missing = Recipes_Ingredients.loc[Recipes_Ingredients["Test"] == 0]
    #Determine what quantity of the items are missing
    Missing["Shopping List"] = Missing["Difference"]
    Missing.loc[pd.isna(Missing["Shopping List"]), "Shopping List"] = Missing.loc[pd.isna(Missing["Shopping List"]), "Generic Amount"]
    x = pd.DataFrame(Missing.groupby("Recipe ID")["Test"].count()).reset_index()
    x.rename(columns = {"Test":"Missing"}, inplace=True)
    y = y.merge(x, how="left", left_on ="Recipe ID", right_on ="Recipe ID")
    y.loc[pd.isna(y["Missing"]),"Missing"] = 0
    y = y.loc[y["Missing"] <= AllowanceI]
    Missing = Missing.drop(columns=["Generic Amount",
                        "Test",
                        "Difference"])
    Missing = Missing.sort_values(by=["Recipe ID"])
    Missing = Missing.loc[Missing["Recipe ID"].isin(y["Recipe ID"])]


RecipeLoad()
RecipeSearch()

print(Missing)
