


document.addEventListener("DOMContentLoaded", async function(){
    const path = window.location.pathname;
    if(path.includes("index.html") || path === "/"){
         let data = await RequestRestaurantInfo()
         addRestaurants(data) 
    }
    if (path.includes("pages.html")) {
     const restaurantJSON = sessionStorage.getItem("CurrentSelected");
     
 
     if (restaurantJSON) {
         const restaurant = JSON.parse(restaurantJSON);
         console.log(restaurant)
         document.getElementById("RestBanner").src = restaurant.imgs;
         menu = document.getElementById("FoodBar");
         foods = restaurant.menu
         console.log(foods)
         foods.forEach(food => {
             let k = document.createElement("div");
             k.classList.add("Items")
             k.classList.add("FoodTab")
             k.innerHTML += "<img src='" + food.Picture + "' />"
             k.innerHTML += "<p>" + food.name + "</p>"
             k.innerHTML += "<p>" + food.price + "</p>"
             menu.appendChild(k)
         })
 
     } else {
         console.warn("No restaurant found in sessionStorage");
     }
 }
    
    
 })
 
 
 
 function addRestaurants(data){
     data.restaurants.forEach(restaurant => {
         let j = document.createElement("div");
         j.classList.add("restaurant_tab");
      
         j.innerHTML += "<img src='" + (restaurant.imgs || "placeholder.jpg") + "' class='display' />";
         j.innerHTML += "<p>" + restaurant.name + "</p>";
         j.addEventListener("click", function() {
             sessionStorage.setItem("CurrentSelected", JSON.stringify(restaurant));
             window.location.href = "pages.html";
             console.log("saved")
         });
         document.querySelector("#Menus").appendChild(j);
     });
     
 }
 
 
 async function RequestRestaurantInfo(){
     try {
         const response = await fetch('http://localhost:8080/api/restaurants');
         if (!response.ok) {
             throw new Error(`HTTP error! status: ${response.status}`);
         }
 
         const data = await response.json();
 
        
       
         console.log(data);
 
         return data;
 
     } catch (error) {
         console.error("Failed to fetch restaurant info:", error);
         return null;
     }
 }