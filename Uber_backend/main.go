package main

import (
	"encoding/json"
	"net/http"
	"database/sql"
    "fmt"
    "log"
	_ "github.com/go-sql-driver/mysql"
	"github.com/rs/cors"
)

type Request struct{
	amount int `json:"amount"`
	addr string `json:"address"`
}



type MenuItem struct {
	Name  string  `json:"name"`
	Price float64 `json:"price"`
	Pic string `json:"Picture"`
}

type Restaurant struct {
	ID          int        `json:"id"`
	Name        string     `json:"name"`
	Tags        []string   `json:"tags"`
	Description string     `json:"description"`
	Menu        []MenuItem `json:"menu"`
	Address 	string		`json:"address"`
	Img         string      `json:"imgs"`
}

type Response struct {
	Restaurants []Restaurant `json:"restaurants"`
}

func main(){
	http.HandleFunc("/api/restaurants", createEXP)
	handler := cors.Default().Handler(http.DefaultServeMux)
	fmt.Println("Server started at http://localhost:8080")
	log.Fatal(http.ListenAndServe(":8080", handler))
}

func connectDB(){
	dsn := "root:Lisa650101@tcp(localhost:3306)/"
	db ,err := sql.Open("mysql", dsn)
	if err != nil{
		log.Fatal("error connecting to DB")
	}
	defer db.Close()
	if err := db.Ping(); err != nil {
		log.Fatal("Error connecting to MySQL:", err)
	}
	fmt.Println("Connected to MySQL successfully!")
	_, err = db.Exec("CREATE DATABASE IF NOT EXISTS UberAPP")
	if err != nil {
		log.Fatal("Error creating database:", err)
	}

	fmt.Println("Database 'UberAPP' created successfully!")
}

func create_User_table(){
	dsn := "root:Lisa650101@tcp(localhost:3306)/UberAPP"
	db, err := sql.Open("mysql", dsn)
	if err != nil {
		log.Fatal("Error opening database:", err)
	}
	defer db.Close()

	query := `CREATE TABLE IF NOT EXISTS users (
		id INT AUTO_INCREMENT PRIMARY KEY,
		name VARCHAR(100) NOT NULL,
		email VARCHAR(100) UNIQUE NOT NULL,
		password varchar(100) NOT NULL,
		created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	)`

	_, err = db.Exec(query)

	if err != nil {
		log.Fatal("Error creating table:", err)
	}

	query := `CREATE TABLE IF NOT EXISTS customers (
		user_id INT PRIMARY KEY REFERENCES users(id),
    	
	)`

	_, err_c = db.Exec(query)

	if err_c != nil{
		log.Fatal("Error creating table:", err)
	}

	query := `CREATE TABLE IF NOT EXISTS favorites (
		user_id INT REFERENCES users(id),
    	fav_restaurant INT REFERENCES restaurants(id),
    	PRIMARY KEY (user_id, fav_restaurant)	
	)`

	_, err_F = db.Exec(query)

	if err_F != nil{
		log.Fatal("Error creating table:", err)
	}

	
	query := `CREATE TABLE IF NOT EXISTS Frequent_address (
		user_id INT REFERENCES users(id),
    	address VARCHAR(100) NOT NULL,
		PRIMARY KEY (user_id, address)	
	)`

	_, err_FA = db.Exec(query)

	if err_FA != nil{
		log.Fatal("Error creating table:", err)
	}


	query := `CREATE TABLE IF NOT EXISTS vendors (
		user_id INT PRIMARY KEY REFERENCES users(id),
    	store INT,
		FOREIGN KEY (store) REFERENCES restaurants(id)
	)`

	_, err_v = db.Exec(query)

	if err_v != nil{
		log.Fatal("Error creating table:", err)
	}

	query := `CREATE TABLE IF NOT EXISTS DeliveryP (
		user_id INT PRIMARY KEY REFERENCES users(id),
    	miles INT NOT NULL,
		lastDeliveryTime TIMESTAMP,
	)`

	_, err_d = db.Exec(query)

	if err_d != nil{
		log.Fatal("Error creating table:", err)
	}

	fmt.Println("Table 'users' and subclasses created successfully!")
}

func create_restaurants_table(){
	dsn := "root:Lisa650101@tcp(localhost:3306)/UberAPP"
	db, err := sql.Open("mysql", dsn)
	if err != nil {
		log.Fatal("Error opening database:", err)
	}
	defer db.Close()

	query := `CREATE TABLE IF NOT EXISTS restaurants (
		id INT AUTO_INCREMENT PRIMARY KEY,
		name VARCHAR(100) NOT NULL,
		Tags VARCHAR(100),
		picture VARCHAR(100),
		
	)`

	_, err = db.Exec(query)

	if err != nil {
		log.Fatal("Error creating table:", err)
	}

	query := `CREATE TABLE IF NOT EXISTS tags (
		id INT AUTO_INCREMENT PRIMARY KEY,
		name VARCHAR(50) UNIQUE,
	)`

	_, err_T = db.Exec(query)

	if err_T != nil {
		log.Fatal("Error creating table:", err)
	}

	
	query := `CREATE TABLE IF NOT EXISTS restaurant_Tags (
		restaurant_id INT REFERENCES restaurants(id),
    	tag_id INT REFERENCES tags(id),
    	PRIMARY KEY (restaurant_id, tag_id)
	)`

	_, err_TR = db.Exec(query)

	if err_TR != nil {
		log.Fatal("Error creating table:", err)
	}

	fmt.Println("Table 'restaurants' and 'Tags' related table created successfully!")
}




func create_foodItem_table(){
	dsn := "root:Lisa650101@tcp(localhost:3306)/UberAPP"
	db, err := sql.Open("mysql", dsn)
	if err != nil {
		log.Fatal("Error opening database:", err)
	}
	defer db.Close()

	query := `CREATE TABLE IF NOT EXISTS Items (
		id INT AUTO_INCREMENT PRIMARY KEY,
		store_id INT NOT NULL,
		name VARCHAR(100) NOT NULL,
		price DECIMAL(10, 2) NOT NULL,
		description TEXT,
		picture VARCHAR(100), 
		FOREIGN KEY (store_id) REFERENCES restaurants(id)
	)`

	_, err = db.Exec(query)

	if err != nil {
		log.Fatal("Error creating table:", err)
	}

	fmt.Println("Table 'Items' created successfully!")
}



func create_orders_table(){
	dsn := "root:Lisa650101@tcp(localhost:3306)/UberAPP"
	db, err := sql.Open("mysql", dsn)
	if err != nil {
		log.Fatal("Error opening database:", err)
	}
	defer db.Close()

	query := `CREATE TABLE IF NOT EXISTS Orders (
		id INT AUTO_INCREMENT PRIMARY KEY,
		user_id INT NOT NULL,
		restaurant_id INT NOT NULL,
		items VARCHAR(100) NOT NULL,
		price INT NOT NULL,
		created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
		ResponsibleDeliveryMan INT NOT NULL,
		FOREIGN KEY (user_id) REFERENCES users(id),
		FOREIGN KEY (restaurant_id) REFERENCES restaurants(id),
		FOREIGN KEY (ResponsibleDeliveryMan) REFERENCES users(id)
	)`

	_, err = db.Exec(query)

	if err != nil {
		log.Fatal("Error creating table:", err)
	}

	fmt.Println("Table 'Items' created successfully!")
}


func createEXP(w http.ResponseWriter, r *http.Request) {
	response := Response{
		Restaurants: []Restaurant{
			{
				ID:   1,
				Name: "Luigi’s Pizzeria",
				Tags: []string{"Italian", "Pizza", "Pasta"},
				Description: "Authentic Italian cuisine with wood-fired pizzas and homemade pasta.",
				Menu: []MenuItem{
					{Name: "Margherita Pizza", Price: 8.99, Pic: "asssets/ex2.jpg"},
					{Name: "Spaghetti Bolognese", Price: 10.50, Pic: "asssets/ex2.jpg"},
				},
				Address: "eqwdsad",
				Img: "asssets/ex.jpg",
			},
			{
				ID:   2,
				Name: "Dragon Wok",
				Tags: []string{"Chinese", "Noodles", "Spicy"},
				Description: "Spicy Sichuan and Cantonese dishes.",
				Menu: []MenuItem{
					{Name: "Kung Pao Chicken", Price: 9.99, Pic: "asssets/ex2.jpg"},
					{Name: "Beef Chow Mein", Price: 11.25, Pic: "asssets/ex2.jpg"},
				},
				Address: "34435",
				Img: "asssets/ex2.jpg",
			},
		},
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}