#install.packages("shiny")
#install.packages("tidyverse")
#install.packages("DT")

library(shiny)
library(tidyverse)
library(DT)

setwd("~/Documents/csv")
marathon <- read_csv("marathon_runs.csv")

glimpse(marathon)
summary(marathon)
View(marathon)

# ---- 2) Define the UI ------------------------------------
# The UI describes what the app *looks like* (layout, inputs, outputs)
ui <- fluidPage(
  
  # App title (top of the page)
  titlePanel("Marathon Performance Explorer"),
  
  # Sidebar layout: filters on the left, outputs on the right
  sidebarLayout(
    
    # ---- Sidebar: user controls --------------------------
    sidebarPanel(
      helpText("Filter the data and explore how age, training, and temperature relate to finish time."),
      
      # Gender filter (with an "All" option)
      selectInput(
        inputId = "gender",
        label = "Gender:",
        choices = c("All", sort(unique(marathon$Gender))),
        selected = "All"
      ),
      
      # Age range filter
      sliderInput(
        inputId = "age_range",
        label = "Age range:",
        min = min(marathon$Age),
        max = max(marathon$Age),
        value = c(min(marathon$Age), max(marathon$Age)),
        step = 1
      ),
      
      # Weekly training miles filter
      sliderInput(
        inputId = "miles_range",
        label = "Weekly training miles:",
        min = min(marathon$WeeklyMiles),
        max = max(marathon$WeeklyMiles),
        value = c(min(marathon$WeeklyMiles), max(marathon$WeeklyMiles)),
        step = 5
      ),
      
      # Variable for x-axis
      selectInput(
        inputId = "xvar",
        label = "X-axis variable:",
        choices = c(
          "Age" = "Age",
          "Weekly miles" = "WeeklyMiles",
          "Race temperature (F)" = "RaceTempF"
        ),
        selected = "Age"
      ),
      
      # Variable for y-axis
      selectInput(
        inputId = "yvar",
        label = "Y-axis variable:",
        choices = c(
          "Finish time (minutes)" = "FinishTimeMin",
          "Pace (min/mile)" = "PaceMinPerMile"
        ),
        selected = "FinishTimeMin"
      ),
      
      # Color aesthetic
      selectInput(
        inputId = "color_by",
        label = "Color points by:",
        choices = c("None", "Gender", "Corral"),
        selected = "Gender"
      ),
      
      # Type of plot
      radioButtons(
        inputId = "plot_type",
        label = "Plot type:",
        choices = c("Scatterplot", "Histogram of finish time", "Boxplot by gender"),
        selected = "Scatterplot"
      )
    ),
    
    # ---- Main panel: outputs -----------------------------
    mainPanel(
      tabsetPanel(
        tabPanel("Plot", plotOutput("main_plot")),
        tabPanel("Summary", verbatimTextOutput("summary_text")),
        tabPanel("Data", DTOutput("data_table"))
      )
    )
  )
)

# ---- 3) Define the server logic ---------------------------
# The server describes how the app *behaves* (what happens
# when inputs change, how outputs get updated)
server <- function(input, output, session) {
  
  # 3a) Reactive filtered data -----------------------------
  # This "reactive" expression returns a filtered version of the
  # dataset based on the user's selections.
  filtered_data <- reactive({
    dat <- marathon
    
    # Filter by gender (only if "All" is NOT selected)
    if (input$gender != "All") {
      dat <- dat %>% 
        filter(Gender == input$gender)
    }
    
    # Filter by age, using the slider range
    dat <- dat %>% 
      filter(
        Age >= input$age_range[1],
        Age <= input$age_range[2]
      )
    
    # Filter by weekly miles
    dat <- dat %>% 
      filter(
        WeeklyMiles >= input$miles_range[1],
        WeeklyMiles <= input$miles_range[2]
      )
    
    dat
  })
  
  # 3b) Main plot output -----------------------------------
  output$main_plot <- renderPlot({
    dat <- filtered_data()   # always use the reactive data
    
    # If no rows after filtering, show a friendly message
    if (nrow(dat) == 0) {
      plot.new()
      title("No data available with current filters.\nTry widening your age or miles range.")
      return()
    }
    
    # Choose the plot type based on the radio button
    if (input$plot_type == "Scatterplot") {
      
      p <- ggplot(dat, aes_string(x = input$xvar, y = input$yvar)) +
        geom_point(aes_string(color = ifelse(input$color_by == "None", "NULL", input$color_by)), alpha = 0.8) +
        labs(x = input$xvar, y = input$yvar) +
        theme_minimal()
      
      # If color_by is "None", remove the legend
      if (input$color_by == "None") {
        p <- p + scale_color_discrete(guide = "none")
      }
      
      p
      
    } else if (input$plot_type == "Histogram of finish time") {
      
      ggplot(dat, aes(x = FinishTimeMin)) +
        geom_histogram(bins = 20) +
        labs(x = "Finish time (minutes)", y = "Count") +
        theme_minimal()
      
    } else {  # "Boxplot by gender"
      
      ggplot(dat, aes(x = Gender, y = FinishTimeMin, fill = Gender)) +
        geom_boxplot() +
        labs(x = "Gender", y = "Finish time (minutes)") +
        theme_minimal() +
        theme(legend.position = "none")
    }
  })
  
  # 3c) Summary text output --------------------------------
  output$summary_text <- renderPrint({
    dat <- filtered_data()
    
    # Show how many runners, and a quick summary of finish time & pace
    cat("Number of runners in filtered data:", nrow(dat), "\n\n")
    cat("Summary of finish time (minutes):\n")
    print(summary(dat$FinishTimeMin))
    cat("\nSummary of pace (min/mile):\n")
    print(summary(dat$PaceMinPerMile))
  })
  
  # 3d) Data table output ----------------------------------
  output$data_table <- renderDT({
    dat <- filtered_data()
    dat
  })
}

shinyApp(ui = ui, server = server)
