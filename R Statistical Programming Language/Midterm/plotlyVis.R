# install.packages("plotly")

library(plotly)
library(ggplot2)

# Volcano Plot #

# Built-in elevation dataset
data(volcano)

# Create 3D surface plot
figs <- plot_ly(
  z = ~volcano,
  type = "surface"
)

figs <- figs %>%
  layout(
    title = "3D Volcano Surface",
    scene = list(
      xaxis = list(title = "X"),
      yaxis = list(title = "Y"),
      zaxis = list(title = "Elevation")
    )
  )

figs

# Starburst Plot #
d1 <- read.csv('https://raw.githubusercontent.com/plotly/datasets/master/coffee-flavors.csv')
d2 <- read.csv('https://raw.githubusercontent.com/plotly/datasets/718417069ead87650b90472464c7565dc8c2cb1c/sunburst-coffee-flavors-complete.csv')
fig2 <- plot_ly() 
fig2 <- fig2 %>%
  add_trace(
    ids = d1$ids,
    labels = d1$labels,
    parents = d1$parents,
    type = 'sunburst',
    maxdepth = 2,
    domain = list(column = 0)
  ) 
fig2 <- fig2 %>%
  add_trace(
    ids = d2$ids,
    labels = d2$labels,
    parents = d2$parents,
    type = 'sunburst',
    maxdepth = 3,
    domain = list(column = 1)
  ) 
fig2 <- fig2 %>%
  layout(
    grid = list(columns =2, rows = 1),
    margin = list(l = 0, r = 0, b = 0, t = 0),
    sunburstcolorway = c(
      "#636efa","#EF553B","#00cc96","#ab63fa","#19d3f3",
      "#e763fa", "#FECB52","#FFA15A","#FF6692","#B6E880"
    ),
    extendsunburstcolors = TRUE)
fig2

# GGplot #
p <- ggplot(dat, aes(x = xvar, y = yvar)) +
  geom_point(shape = 1) +
  geom_smooth(method = lm)

ggplotly(p)

# Histogram #

ster <- read.csv("C:/Users/kscot/Downloads/Steroid_Use_Study.csv", header=T)

ster$Group <- factor(ster$Group, levels = c("High School", "College"))
ster$Gender <- factor(ster$Gender, levels = c("Male", "Female"))
ster$Athlete <- factor(ster$Athlete, levels = c("Yes", "No"))

ID <- ster$ID
Group <- ster$Group
Gender <- ster$Gender
Age <- ster$Age
Athlete <- ster$Athlete
Willingness <- ster$Willingness
PeerInfulence <- ster$PeerInfluence
Knowledge <- ster$Knowledge
PerceivedRisk <- ster$PerceivedRisk

fig <- plot_ly(alpha = 0.6)

fig <- fig %>%
  add_histogram(
    x = ~PerceivedRisk,   # first variable
    name = "Perceived Risk"    # appears first in legend
  ) %>%
  add_histogram(
    x = ~PeerInfulence,   # second variable
    name = "Peer Influence"    # appears second in legend
  ) %>%
  layout(
    barmode = "overlay",
    title = "Stacked Bar Chart: Peer Influence vs Perceived Risk",
    xaxis = list(title = "Score"),
    yaxis = list(title = "Count"),
    legend = list(title = list(text = "Variables"))  # adds a legend title
  )

fig
