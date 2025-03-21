#include <Wire.h>
#include <DHT.h>
#include <OneWire.h>
#include <DallasTemperature.h>

#define I2C_ADDRESS 0x20  // Unique I2C address for this Arduino

#define DHTPIN 2
#define DHTTYPE DHT22
DHT dht(DHTPIN, DHTTYPE);

#define DS18B20_PIN 4
OneWire oneWire(DS18B20_PIN);
DallasTemperature sensors(&oneWire);

#define SOIL_SENSOR_PIN A0

float temperatureDHT = 0, humidityDHT = 0;
float temperatureDS18B20 = 0;
int soilMoisture = 0;

void setup() {
    Wire.begin(I2C_ADDRESS);  // Join I2C bus as slave
    Wire.onRequest(requestEvent);

    dht.begin();
    sensors.begin();

    Serial.begin(9600);               // Initialize Serial for debugging (9600 baud)
}

void loop() {
    // Read sensors
    humidityDHT = dht.readHumidity();
    temperatureDHT = dht.readTemperature();
    
    sensors.requestTemperatures();
    temperatureDS18B20 = sensors.getTempCByIndex(0);
    
    soilMoisture = analogRead(SOIL_SENSOR_PIN);

    delay(500);  // Slow update rate


    // Print sensor readings to Serial Monitor
    Serial.println("Envoriment:");

    Serial.print("Temp: ");
    Serial.print(temperatureDHT);
    Serial.print(" °C, Humidity: ");
    Serial.print(humidityDHT);
    Serial.print(" %");
    Serial.println("");
    
    Serial.println("Soil:");
    Serial.print("Temp: ");
    Serial.print(temperatureDS18B20);
    Serial.print(" °C");
    Serial.print(" Moisture: ");
    Serial.print(soilMoisture);
    Serial.println("");
    Serial.println("");
}

// Send data to Raspberry Pi upon request
void requestEvent() {
    Wire.write((byte*)&temperatureDHT, sizeof(temperatureDHT));
    Wire.write((byte*)&humidityDHT, sizeof(humidityDHT));
    Wire.write((byte*)&temperatureDS18B20, sizeof(temperatureDS18B20));
    Wire.write((byte*)&soilMoisture, sizeof(soilMoisture));
}
