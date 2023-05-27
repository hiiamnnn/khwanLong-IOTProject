#include <dummy.h>

#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <math.h>
#include <ESP8266WiFi.h>
#include <DHT.h>

#define WIFI_SSID "xxxxxxxxx"
#define WIFI_PASSWORD "xxxxxxxx"
#define MQTT_SERVER "192.168.xxx.xx"

// const int Temp_PIN = A0;
// const int MQ135_PIN = D0;
// const int FLAME_SENSOR_PIN = D1;
// const int LED_GREEN = D2;
// const int LED_RED = D3;
// const int LED_Temp = D4;
// const int BUZZER_PIN = D5;
// const char* MQ135Result;
// const char* flameResult;

// #define Temp_PIN A0
#define DHTPIN 15
#define DHTTYPE DHT22

#define MQ135_PIN A0
#define FLAME_SENSOR_PIN 5
#define LED_GREEN 4
#define LED_RED 0
#define LED_Temp 2
#define BUZZER_PIN 14

const char* MQ135Result;
const char* flameResult;

DHT dht(DHTPIN, DHTTYPE);

// Create an instance of the PubSubClient
WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);

double Thermistor(int RawADC) 
{
  double Cal;
  Cal = log(10000.0/((1024.0/RawADC-1))); 
  Cal = 1 / (0.001129148 + (0.000234125 + (0.0000000876741 * Cal * Cal ))* Cal );
  Cal = Cal - 273.15;            // Convert Kelvin to Celcius
  return Cal;
}

void setup() {
  analogReference(DEFAULT);
  Serial.begin(115200);
  pinMode(MQ135_PIN, INPUT);
  // pinMode(Temp_PIN, INPUT);
  pinMode(FLAME_SENSOR_PIN, INPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(LED_Temp, OUTPUT);
  pinMode(LED_GREEN, OUTPUT);
  pinMode(LED_RED, OUTPUT);
  digitalWrite(LED_Temp, LOW);

  // Connect to Wi-Fi
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  while (WiFi.status() != WL_CONNECTED) {
    delay(5000);
    Serial.println("Connecting to WiFi...");
  }
  Serial.println("Connected to WiFi");

  // Connect to mosquitto
  mqttClient.setServer(MQTT_SERVER, 1883);
  while (!mqttClient.connected()) {
    if (mqttClient.connect("ESP8266Client")) {
      Serial.println("Connected to MQTT broker!");
    } else {
      Serial.println("Failed to connect to MQTT broker, retrying...");
      delay(5000);
    }
  }

  dht.begin();
}

void loop() {
  mqttClient.loop();
  // MQ135
  int MQ135Value = analogRead(MQ135_PIN); //digitalRead(MQ135_PIN);
  Serial.println(MQ135Value);
  if (MQ135Value >= 400) {
    MQ135Result = "Gas detected!";
    Serial.println(MQ135Result);
    digitalWrite(LED_GREEN, LOW);
    digitalWrite(LED_RED, HIGH);
  }
  else {
    MQ135Result = "Gas not detected";
    Serial.println(MQ135Result);
    digitalWrite(LED_RED, LOW);
    digitalWrite(LED_GREEN, HIGH);
  }
  mqttClient.publish("sensor/mq135", MQ135Result);

  // temp
  // float Temp=Thermistor(analogRead(Temp_PIN));

  float Temp = dht.readTemperature();
  Serial.print(Temp);
  Serial.println(" C");
  if(Temp >= 50) {
    digitalWrite(LED_Temp, HIGH);
    delay(200);
    digitalWrite(LED_Temp, LOW);
    delay(200);
    digitalWrite(LED_Temp, HIGH);
    delay(200);
    digitalWrite(LED_Temp, LOW);
    delay(200);
    digitalWrite(LED_Temp, HIGH);
    delay(200);
    digitalWrite(LED_Temp, LOW);
    delay(200);
    digitalWrite(LED_Temp, HIGH);
    delay(200);
    digitalWrite(LED_Temp, LOW);
    delay(200);
  }

  // Convert from float to char
  char tempResult[10];
  dtostrf(Temp, 6, 2, tempResult);
  mqttClient.publish("sensor/temp", tempResult);

  // flameSensor
  int flameDetected = digitalRead(FLAME_SENSOR_PIN);
  Serial.println(flameDetected);
  if (flameDetected == 1) {
    flameResult = "Flame detected!";
    Serial.println(flameResult);
    // digitalWrite(BUZZER_PIN, HIGH);
    analogWrite(BUZZER_PIN, 128);
    delay(1000);
  } else {
    flameResult = "No flame detected";
    Serial.println(flameResult);
    //digitalWrite(BUZZER_PIN, LOW);
    analogWrite(BUZZER_PIN, 0);
    delay(1000);
  }
  mqttClient.publish("sensor/flame", flameResult);
  // wait for 1 second before checking again
  delay(1000);
}