#!/usr/bin/env python3
"""
Weather Widget for Marina
Displays a brief weather summary and expands to a detailed view
"""

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import threading
import time
from datetime import datetime
from gui.components.weather_service import WeatherService

class WeatherWidget:
    def __init__(self, parent_frame, theme_manager):
        self.parent_frame = parent_frame
        self.theme_manager = theme_manager
        self.weather_service = WeatherService()
        
        # Weather data
        self.current_weather = None
        self.forecast_data = None
        
        # Create the widget
        self.create_widget()
        
        # Load initial weather data
        self.load_weather_data()
        
    def create_widget(self):
        """Create the main weather display widget"""
        # Create a compact weather display frame
        self.weather_frame = ttk.LabelFrame(self.parent_frame, text="🌤️ Weather", padding=5)
        self.weather_frame.pack(fill="x", padx=5, pady=5)
        
        # Current weather display
        self.weather_content = ttk.Frame(self.weather_frame)
        self.weather_content.pack(fill="x")
        
        # Temperature display
        self.temp_label = ttk.Label(
            self.weather_content, 
            text="Loading...", 
            font=("Ubuntu", 14, "bold"),
            foreground="#4CAF50"
        )
        self.temp_label.pack(side="left")
        
        # Weather description
        self.desc_label = ttk.Label(
            self.weather_content,
            text="",
            font=("Ubuntu", 10),
            foreground="#888888"
        )
        self.desc_label.pack(side="left", padx=(10, 0))
        
        # Location
        self.location_label = ttk.Label(
            self.weather_content,
            text="",
            font=("Ubuntu", 9),
            foreground="#666666"
        )
        self.location_label.pack(side="left", padx=(10, 0))
        
        # Location refresh button
        self.location_refresh_button = ttk.Button(
            self.weather_content,
            text="📍",
            command=self.refresh_location,
            width=3
        )
        self.location_refresh_button.pack(side="right", padx=(0, 5))
        
        # Details button
        self.details_button = ttk.Button(
            self.weather_content,
            text="Details",
            command=self.open_weather_details,
            width=8
        )
        self.details_button.pack(side="right")
        
        # Refresh button
        self.refresh_button = ttk.Button(
            self.weather_content,
            text="🔄",
            command=self.refresh_weather,
            width=3
        )
        self.refresh_button.pack(side="right", padx=(0, 5))
        
    def load_weather_data(self):
        """Load weather data in background thread"""
        def fetch_data():
            try:
                # Fetch current weather
                self.current_weather = self.weather_service.get_current_weather()
                
                # Fetch forecast
                self.forecast_data = self.weather_service.get_forecast()
                
                # Update display on main thread
                self.parent_frame.after(0, self.update_display)
                
            except Exception as e:
                print(f"Error loading weather data: {e}")
                self.parent_frame.after(0, self.show_error)
        
        # Run in background thread
        thread = threading.Thread(target=fetch_data, daemon=True)
        thread.start()
        
    def update_display(self):
        """Update the weather display with current data"""
        if not self.current_weather:
            return
            
        try:
            # Update temperature
            temp = self.current_weather['main']['temp']
            self.temp_label.config(text=self.weather_service.format_temperature(temp))
            
            # Update description
            desc = self.current_weather['weather'][0]['description'].title()
            self.desc_label.config(text=desc)
            
            # Update location
            location = self.current_weather['name']
            self.location_label.config(text=location)
            
        except Exception as e:
            print(f"Error updating weather display: {e}")
            self.show_error()
            
    def show_error(self):
        """Show error state"""
        self.temp_label.config(text="Error")
        self.desc_label.config(text="Unable to load weather")
        self.location_label.config(text="")
        
    def refresh_weather(self):
        """Refresh weather data"""
        self.temp_label.config(text="Refreshing...")
        self.desc_label.config(text="")
        self.location_label.config(text="")
        self.load_weather_data()
        
    def refresh_location(self):
        """Refresh location and weather data"""
        self.temp_label.config(text="Updating location...")
        self.desc_label.config(text="")
        self.location_label.config(text="Detecting location...")
        
        def update_location():
            try:
                self.weather_service.refresh_location()
                self.parent_frame.after(0, self.load_weather_data)
            except Exception as e:
                print(f"Error refreshing location: {e}")
                self.parent_frame.after(0, self.show_error)
        
        # Run in background thread
        thread = threading.Thread(target=update_location, daemon=True)
        thread.start()
        
    def open_weather_details(self):
        """Open detailed weather view"""
        if not self.current_weather or not self.forecast_data:
            messagebox.showwarning("Weather Details", "Weather data not available. Please try refreshing.")
            return
            
        # Create detailed weather window
        WeatherDetailsWindow(self.parent_frame, self.theme_manager, self.current_weather, self.forecast_data, self.weather_service)

class WeatherDetailsWindow:
    def __init__(self, parent, theme_manager, current_weather, forecast_data, weather_service):
        self.parent = parent
        self.theme_manager = theme_manager
        self.current_weather = current_weather
        self.forecast_data = forecast_data
        self.weather_service = weather_service
        
        # Create the window
        self.create_window()
        
    def create_window(self):
        """Create the detailed weather window"""
        self.window = tk.Toplevel(self.parent)
        self.window.title("Weather Details")
        self.window.geometry("800x600")
        self.window.resizable(True, True)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Current weather tab
        self.create_current_tab()
        
        # Forecast tab
        self.create_forecast_tab()
        
        # Charts tab
        self.create_charts_tab()
        
    def create_current_tab(self):
        """Create current weather tab"""
        current_frame = ttk.Frame(self.notebook)
        self.notebook.add(current_frame, text="Current Weather")
        
        # Main info frame
        main_frame = ttk.LabelFrame(current_frame, text="Current Conditions", padding=10)
        main_frame.pack(fill="x", padx=10, pady=10)
        
        # Temperature info
        temp_frame = ttk.Frame(main_frame)
        temp_frame.pack(fill="x", pady=5)
        
        temp = self.current_weather['main']['temp']
        feels_like = self.current_weather['main']['feels_like']
        temp_min = self.current_weather['main']['temp_min']
        temp_max = self.current_weather['main']['temp_max']
        
        ttk.Label(temp_frame, text="Temperature:", font=("Ubuntu", 12, "bold")).pack(side="left")
        ttk.Label(temp_frame, text=self.weather_service.format_temperature(temp), 
                 font=("Ubuntu", 12)).pack(side="left", padx=(10, 0))
        
        ttk.Label(temp_frame, text=f"Feels like {self.weather_service.format_temperature(feels_like)}", 
                 font=("Ubuntu", 10)).pack(side="left", padx=(20, 0))
        
        # Min/Max temperatures
        minmax_frame = ttk.Frame(main_frame)
        minmax_frame.pack(fill="x", pady=5)
        
        ttk.Label(minmax_frame, text="Min/Max:", font=("Ubuntu", 11, "bold")).pack(side="left")
        ttk.Label(minmax_frame, text=f"{self.weather_service.format_temperature(temp_min)} / {self.weather_service.format_temperature(temp_max)}", 
                 font=("Ubuntu", 11)).pack(side="left", padx=(10, 0))
        
        # Weather description
        desc_frame = ttk.Frame(main_frame)
        desc_frame.pack(fill="x", pady=5)
        
        desc = self.current_weather['weather'][0]['description'].title()
        ttk.Label(desc_frame, text="Condition:", font=("Ubuntu", 11, "bold")).pack(side="left")
        ttk.Label(desc_frame, text=desc, font=("Ubuntu", 11)).pack(side="left", padx=(10, 0))
        
        # Additional info frame
        info_frame = ttk.LabelFrame(current_frame, text="Additional Information", padding=10)
        info_frame.pack(fill="x", padx=10, pady=10)
        
        # Humidity
        humidity_frame = ttk.Frame(info_frame)
        humidity_frame.pack(fill="x", pady=3)
        ttk.Label(humidity_frame, text="Humidity:", font=("Ubuntu", 10, "bold")).pack(side="left")
        ttk.Label(humidity_frame, text=self.weather_service.format_humidity(self.current_weather['main']['humidity']), 
                 font=("Ubuntu", 10)).pack(side="left", padx=(10, 0))
        
        # Pressure
        pressure_frame = ttk.Frame(info_frame)
        pressure_frame.pack(fill="x", pady=3)
        ttk.Label(pressure_frame, text="Pressure:", font=("Ubuntu", 10, "bold")).pack(side="left")
        ttk.Label(pressure_frame, text=self.weather_service.format_pressure(self.current_weather['main']['pressure']), 
                 font=("Ubuntu", 10)).pack(side="left", padx=(10, 0))
        
        # Wind
        wind_frame = ttk.Frame(info_frame)
        wind_frame.pack(fill="x", pady=3)
        ttk.Label(wind_frame, text="Wind:", font=("Ubuntu", 10, "bold")).pack(side="left")
        ttk.Label(wind_frame, text=self.weather_service.format_wind_speed(self.current_weather['wind']['speed']), 
                 font=("Ubuntu", 10)).pack(side="left", padx=(10, 0))
        
        # Visibility
        visibility_frame = ttk.Frame(info_frame)
        visibility_frame.pack(fill="x", pady=3)
        ttk.Label(visibility_frame, text="Visibility:", font=("Ubuntu", 10, "bold")).pack(side="left")
        ttk.Label(visibility_frame, text=f"{self.current_weather['visibility']/1000:.1f} km", 
                 font=("Ubuntu", 10)).pack(side="left", padx=(10, 0))
        
        # Sun times
        sun_frame = ttk.LabelFrame(current_frame, text="Sun Times", padding=10)
        sun_frame.pack(fill="x", padx=10, pady=10)
        
        sunrise = datetime.fromtimestamp(self.current_weather['sys']['sunrise']).strftime('%H:%M')
        sunset = datetime.fromtimestamp(self.current_weather['sys']['sunset']).strftime('%H:%M')
        
        sunrise_frame = ttk.Frame(sun_frame)
        sunrise_frame.pack(fill="x", pady=3)
        ttk.Label(sunrise_frame, text="Sunrise:", font=("Ubuntu", 10, "bold")).pack(side="left")
        ttk.Label(sunrise_frame, text=sunrise, font=("Ubuntu", 10)).pack(side="left", padx=(10, 0))
        
        sunset_frame = ttk.Frame(sun_frame)
        sunset_frame.pack(fill="x", pady=3)
        ttk.Label(sunset_frame, text="Sunset:", font=("Ubuntu", 10, "bold")).pack(side="left")
        ttk.Label(sunset_frame, text=sunset, font=("Ubuntu", 10)).pack(side="left", padx=(10, 0))
        
    def create_forecast_tab(self):
        """Create forecast tab"""
        forecast_frame = ttk.Frame(self.notebook)
        self.notebook.add(forecast_frame, text="5-Day Forecast")
        
        # Create scrollable frame
        canvas = tk.Canvas(forecast_frame)
        scrollbar = ttk.Scrollbar(forecast_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Process forecast data by day
        daily_forecasts = self.group_forecast_by_day()
        
        for day, forecasts in daily_forecasts.items():
            day_frame = ttk.LabelFrame(scrollable_frame, text=day, padding=10)
            day_frame.pack(fill="x", padx=10, pady=5)
            
            for forecast in forecasts[:4]:  # Show first 4 forecasts of the day
                forecast_item = ttk.Frame(day_frame)
                forecast_item.pack(fill="x", pady=2)
                
                # Time
                time_str = datetime.fromtimestamp(forecast['dt']).strftime('%H:%M')
                ttk.Label(forecast_item, text=time_str, font=("Ubuntu", 10, "bold"), width=8).pack(side="left")
                
                # Temperature
                temp_str = self.weather_service.format_temperature(forecast['main']['temp'])
                ttk.Label(forecast_item, text=temp_str, font=("Ubuntu", 10), width=8).pack(side="left")
                
                # Description
                desc = forecast['weather'][0]['description'].title()
                ttk.Label(forecast_item, text=desc, font=("Ubuntu", 10), width=20).pack(side="left")
                
                # Humidity
                humidity = self.weather_service.format_humidity(forecast['main']['humidity'])
                ttk.Label(forecast_item, text=humidity, font=("Ubuntu", 10), width=8).pack(side="left")
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
    def create_charts_tab(self):
        """Create charts tab"""
        charts_frame = ttk.Frame(self.notebook)
        self.notebook.add(charts_frame, text="Charts & Analysis")
        
        # Temperature trend
        temp_frame = ttk.LabelFrame(charts_frame, text="Temperature Trend (Next 24 Hours)", padding=10)
        temp_frame.pack(fill="x", padx=10, pady=10)
        
        # Simple text-based chart
        chart_text = tk.Text(temp_frame, height=10, width=80, font=("Courier", 10))
        chart_text.pack(fill="both", expand=True)
        
        # Generate simple temperature chart
        chart_content = self.generate_temperature_chart()
        chart_text.insert(tk.END, chart_content)
        chart_text.config(state=tk.DISABLED)
        
        # Weather summary
        summary_frame = ttk.LabelFrame(charts_frame, text="Weather Summary", padding=10)
        summary_frame.pack(fill="x", padx=10, pady=10)
        
        summary_text = tk.Text(summary_frame, height=8, width=80, font=("Ubuntu", 10))
        summary_text.pack(fill="both", expand=True)
        
        summary_content = self.generate_weather_summary()
        summary_text.insert(tk.END, summary_content)
        summary_text.config(state=tk.DISABLED)
        
    def group_forecast_by_day(self):
        """Group forecast data by day"""
        daily_forecasts = {}
        
        for forecast in self.forecast_data['list']:
            date = datetime.fromtimestamp(forecast['dt']).strftime('%Y-%m-%d')
            day_name = datetime.fromtimestamp(forecast['dt']).strftime('%A, %B %d')
            
            if day_name not in daily_forecasts:
                daily_forecasts[day_name] = []
            
            daily_forecasts[day_name].append(forecast)
        
        return daily_forecasts
        
    def generate_temperature_chart(self):
        """Generate a simple text-based temperature chart"""
        chart_lines = []
        chart_lines.append("Temperature Trend (°C)")
        chart_lines.append("=" * 50)
        
        # Get next 8 forecasts (24 hours)
        forecasts = self.forecast_data['list'][:8]
        
        for forecast in forecasts:
            time_str = datetime.fromtimestamp(forecast['dt']).strftime('%H:%M')
            temp = forecast['main']['temp']
            
            # Simple bar chart using characters
            bar_length = max(1, int(temp / 2))  # Scale temperature to bar length
            bar = '█' * bar_length
            
            line = f"{time_str:>5} │ {temp:>5.1f}°C │ {bar}"
            chart_lines.append(line)
        
        return "\n".join(chart_lines)
        
    def generate_weather_summary(self):
        """Generate weather summary"""
        summary_lines = []
        
        # Current conditions summary
        current_temp = self.current_weather['main']['temp']
        current_desc = self.current_weather['weather'][0]['description']
        location = self.current_weather['name']
        
        summary_lines.append(f"Current Weather in {location}:")
        summary_lines.append(f"Temperature: {self.weather_service.format_temperature(current_temp)}")
        summary_lines.append(f"Condition: {current_desc.title()}")
        summary_lines.append("")
        
        # Today's forecast summary
        today_forecasts = self.forecast_data['list'][:8]
        temps = [f['main']['temp'] for f in today_forecasts]
        min_temp = min(temps)
        max_temp = max(temps)
        
        summary_lines.append("Today's Forecast:")
        summary_lines.append(f"Temperature Range: {self.weather_service.format_temperature(min_temp)} - {self.weather_service.format_temperature(max_temp)}")
        
        # Most common weather condition today
        conditions = [f['weather'][0]['main'] for f in today_forecasts]
        most_common = max(set(conditions), key=conditions.count)
        summary_lines.append(f"Predominant Condition: {most_common}")
        
        summary_lines.append("")
        summary_lines.append("Weather data provided by OpenWeatherMap")
        summary_lines.append(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        
        return "\n".join(summary_lines)

