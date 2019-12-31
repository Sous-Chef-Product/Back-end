library(readxl)
library(ggplot2)
library(wesanderson)

RecipeLoad <- function(){
start <- Sys.time()  
file <- "Recipes.xlsx"

Recipes_Tools <- read_excel(file, 
                            sheet = "Recipes (Tools)")
Recipes_Ingredients <- read_excel(file,  
                            sheet = "Recipes (Ingredients)")
Recipes_Details <<- read_excel(file, 
                                  sheet = "Recipes (Details)")
Conversions <<- read_excel(file, 
                          sheet = "Conversion Table") 

x <- merge(Recipes_Ingredients, Conversions, by = "Units", all.x = T )
x$Liters <- x$Liters*x$Quantity
x$Grams <- x$Grams*x$Quantity
x$GenericType <- x$Units
x$GenericType[!is.na(x$Grams)] <- "Grams"
x$GenericType[!is.na(x$Liters)] <- "Liters"
x$Items <- 0
x$Items[is.na(x$Grams) & is.na(x$Liters)] <- x$Quantity[is.na(x$Grams) & is.na(x$Liters)]
x$Liters[is.na(x$Liters)] <- 0
x$Grams[is.na(x$Grams)] <- 0
x$Generic <- x$Liters + x$Grams + x$Items
x$Units <- NULL
x$Quantity <- NULL
Recipes_Ingredients <<- x
print(Sys.time() - start)
}
RecipeSearch <- function(AllowanceP = .0,AllowanceI = 1){
  start <- Sys.time()  
  file <- "Recipes.xlsx"
  Profiles_Tools <- read_excel(file, 
                                sheet = "Profile (Tools)")
  Profiles_Ingredients <- read_excel(file, 
                                      sheet = "Profile (Ingredients)")
  Profiles_Preferences <- read_excel(file,  
                                      sheet = "Profile (Preferences)")
##### Standardize Measurements ####
x <- merge(Profiles_Ingredients, Conversions, by = "Units", all.x = T )
x$Liters <- x$Liters*x$Quantity
x$Grams <- x$Grams*x$Quantity
x$GenericType <- x$Units
x$GenericType[!is.na(x$Grams)] <- "Grams"
x$GenericType[!is.na(x$Liters)] <- "Liters"
x$Items <- 0
x$Items[!(x$Units %in% c("Grams","Liters"))] <- x$Quantity[!(x$Units %in% c("Grams","Liters"))]
x$Liters[is.na(x$Liters)] <- 0
x$Grams[is.na(x$Grams)] <- 0
x$Generic <- x$Liters + x$Grams + x$Items
x$Units <- NULL
x$Quantity <- NULL
y <- aggregate(Generic ~ Ingredient, data = x, FUN = sum)
x <- merge(x,y, by = "Ingredient")
x$Generic <- x$Generic.y
x$Generic.x <- NULL
x$Generic.y <- NULL
x$Items <- NULL
Profiles_Ingredients <- unique(x)

x <- merge(Profiles_Ingredients,Recipes_Ingredients, by = "Ingredient", all.y = T)
x$Test <- 0
x$Test[x$Generic.x >= x$Generic.y] <- 1
x$Difference <- x$Generic.y - x$Generic.x
x$Liters.x <- NULL
x$Grams.x <- NULL
x$Items.x <- NULL
x$Generic.x <- NULL
x$GenericType.x <- NULL
x$Liters.y <- NULL
x$Grams.y <- NULL
x$Items.y <- NULL
x$Items <- NULL

Recipes_Ingredients <- x
colnames(Recipes_Ingredients) <- c("Ingredient", "User ID", "Recipe ID", "Importance","Generic Type","Generic","Test","Difference")
  

Percentage <- aggregate(Recipes_Ingredients$Test, by = list(Recipes_Ingredients$`Recipe ID`), FUN = mean)
colnames(Percentage) <- c("Recipe ID","Percentage")
Percentage <- merge(Percentage,Recipes_Details)
Percentage <- Percentage[order(Percentage$Type,-Percentage$Percentage),]
Percentage$Type <- NULL
Percentage <- unique(Percentage)
#Percentage of Items
Percentage <- Percentage[Percentage$Percentage >= AllowanceP,]
Missing <- subset(Recipes_Ingredients, Recipes_Ingredients$Test==0)
Missing$Shopping <- ifelse(is.na(Missing$Difference),Missing$Generic,Missing$Difference)
x <- aggregate(Missing$Test, by = list(Missing$`Recipe ID`), FUN = length)
colnames(x) <- c("Recipe ID","Missing")
Percentage <- merge(Percentage,x,by = "Recipe ID",all.x = T)
Percentage$Missing[is.na(Percentage$Missing)] <- 0
Percentage <- Percentage[Percentage$Missing <= AllowanceI,]

pal <- wes_palette("GrandBudapest2", nrow(Percentage), type = "continuous")
#p <- ggplot(data=Percentage, aes(x=reorder(`Recipe Name`,Percentage), y=Percentage, fill = `Recipe Name`)) +
#  geom_bar(stat = "identity", col = "black") + xlab("Recipe") +
#  scale_y_continuous(labels = scales::percent, limits = c(0,1))  + guides(fill = F) + coord_flip() + theme_classic()
Missing$Generic <- NULL
Missing$Test <- NULL
Missing$Difference <- NULL
Missing <- Missing[order(Missing$`Recipe ID`),]
Missing <- subset(Missing, `Recipe ID` %in% Percentage$`Recipe ID`)
Time <- Sys.time() - start
return(list(Time, Percentage, Missing))
}

RecipeLoad()

RecipeSearch(AllowanceI = 1)

