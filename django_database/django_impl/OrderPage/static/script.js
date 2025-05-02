console.log("script.js loaded!");
let lastSent = 0; 
const interval = 5 * 1000; 
let deliverySocket;
let map;
let marker;
document.addEventListener("DOMContentLoaded", function(){
        
        let tabs = document.querySelectorAll(".restaurant_tab")
        if(tabs.length > 0){
            let userid = document.getElementById("Menus").dataset.user
            const socket = new WebSocket(`ws://${window.location.host}/ws/notify/${userid}/`);
            socket.onmessage = function(e) {
                const data = JSON.parse(e.data);
                console.log('Update received:', data.message);
                loadNewInbox(userid)
            };
            
            socket.onclose = function(e) {
                console.error('WebSocket closed unexpectedly');
            };
            tabs.forEach(tab => {
                tab.addEventListener("click", function(){
                    const id = tab.dataset.id;
                    window.location.href = "/pages/" + parseInt(id) +"/"
                })
            })
        }
        let inbox = document.getElementById("msgToggle")
        if(inbox){
            let drop = document.getElementById("InboxDropdown")
            inbox.addEventListener("click", function(){
                drop.style.display = drop.style.display === "none" ? "block" : "none"
            })
            document.addEventListener("click", (event) => {
                if (!inbox.contains(event.target) && !drop.contains(event.target)) {
                    drop.style.display = "none";
                }
            });
            viewBtn = document.getElementById("viewAll")
            if(viewBtn){
                let user = viewBtn.getAttribute("data-user")
                viewBtn.addEventListener("click", function(){
                    window.location.href = "/Inbox/" + parseInt(user)
                })
            }
        }
        let fav = document.querySelector("#Favorite")
        if(fav){
            fav.addEventListener("click", function(){
                const userID = fav.dataset.id
                window.location.href = "/"  + parseInt(userID) + "/" + "favorite/"
            })
        }
        let order = document.querySelector("#order")
        if(order){
            order.addEventListener("click", function(){
                const userID = order.dataset.id
                window.location.href = "/" + "order" + "/" + parseInt(userID)
            })
        }

        let ShowItemModal = document.querySelectorAll(".Showitems")
        if(ShowItemModal.length > 0){
            let mo = document.querySelector("#myModal")
            let co = document.querySelector("#modalContent")
            let close = document.querySelector(".close")
            if(close){
                close.addEventListener("click", function(){
                    mo.style.display = "none"
                })
            }
       
            ShowItemModal.forEach(Mod => {
                Mod.addEventListener("click", function(){
                    const items = JSON.parse(this.dataset.items); 
                    co.innerHTML = ""; 

                    items.forEach(item => {
                    const p = document.createElement("p");
                    p.textContent = item;
                    co.appendChild(p);
                    });
                    mo.style.display = "flex"
                })

            })
            window.onclick = (e) => {
                if (e.target == mo) {
                  mo.style.display = "none";
                }
              };
        }
        
        let user_roles = document.getElementById("test_roles")
        if(user_roles){
            user_roles.addEventListener("submit", function(e){
                e.preventDefault()
                let form = user_roles.querySelector('input[name="role"]:checked')
                if(form){
                    window.location.href = "/index/" + form.value +"/";
                } else{
                    alert("Please select a role.");
                }
            })
        }
        let deli = document.getElementById("deliverys")
        if(deli){
            let orders = document.querySelectorAll(".OrdersTab")
            orders.forEach(order => {
                order.addEventListener("click", function(){
                    window.location.href = "/deliveryDetails/" + order.dataset.user + "/" + parseInt(order.dataset.id)

                })
            })
            let current = document.getElementById("CurrentOrder")
            if(current){
                current.addEventListener("click", function(){
                    window.location.href = "/CurrentDelivery/" + current.dataset.user
                })
            }
        }

        let button = document.getElementById('TakeOrderBtn');
        if(button){
            button.addEventListener("click", function(){
                let orderId = button.getAttribute('data-order-id');
                let DeliP = button.getAttribute('data-user')
                fetch('/takeorder/' + orderId + '/' + DeliP, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken')
                    },
                    body: JSON.stringify({})
                })
                .then(response => {
                    if (response.ok) {
                        alert('Order taken!');
                        button.disabled = true;
                        button.textContent = 'Order Taken';
                    } else {
                        alert('Failed to take order');
                    }
                    window.location.href = "/index"
                });

            })

        }
        let ShowModal = document.querySelectorAll(".ShowCurrentOrderItems")
  
        if(ShowModal.length > 0){
            let mo = document.querySelector("#DeliModal")
            let co = document.querySelector("#DelimodalContent")
            let close = mo.querySelector(".close");
        if(close){
            
            close.addEventListener("click", function(){
                
                mo.style.display = "none"
            })
        }
   
        ShowModal.forEach(Mod => {
            Mod.addEventListener("click", function(){
                
                const items = JSON.parse(this.dataset.items); 
               
             
                co.innerHTML = ""; 

                items.forEach(item => {
                const p = document.createElement("p");
                p.textContent = item.name + ":" + item.price;
                co.appendChild(p);
                });
                mo.style.display = "flex"
            })

        })
        window.onclick = (e) => {
            if (e.target == mo) {
              mo.style.display = "none";
            }
          };
        }

        let vendorOrder = document.getElementById("Orders")
        if(vendorOrder){
            const protocol = window.location.protocol === "https:" ? "wss://" : "ws://";
            const socket = new WebSocket(protocol + window.location.host + "/ws/orders/");
            socket.onopen = function(e) {
                console.log("WebSocket connection established.");
            }
            socket.onmessage = function(e) {
                const data = JSON.parse(e.data);
                console.log('Update received:', data.message);
                loadOrders(vendorOrder.getAttribute("data-id"));
            };
            socket.onerror = function(error) {
                console.error("WebSocket Error:", error);
            }
            let orders = document.querySelectorAll(".OrdersTab")
            orders.forEach(order => {
                order.addEventListener("click", function(){
                    let oid = this.dataset.id
                    window.location.href = "/VendorOrderDetails/" + oid + "/" + this.dataset.user

                })
            })
        }
        let completeOrder = document.querySelectorAll('.CompleteFoodBtn')
        if(completeOrder.length > 0){
            completeOrder.forEach(btn => {
               
                btn.addEventListener("click", function(){
                    let oid = this.dataset.orderId
                    console.log(oid)
                    fetch('/PrepareOrder/' + parseInt(oid), {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': getCookie('csrftoken')
                        },
                        body: JSON.stringify({})
                    })
                    .then(response => {
                        if (response.ok) {
                            alert('Order completed!');
                            btn.disabled = true;
                            btn.textContent = 'Order finished';
                        } else {
                            alert('Failed to complete order');
                        }
                        window.location.href = "/index"
                    });
                })
            })
        }
        let completeDelivery = document.querySelectorAll('.CompleteOrderBtn')
        if(completeDelivery){
            completeDelivery.forEach(CB => {
                CB.addEventListener("click", function(){
                    let orderId = CB.getAttribute('data-order-id');
                    let Customer = CB.getAttribute('data-customer')
                    fetch('/CompleteOrder/' + parseInt(orderId) + '/' + parseInt(Customer), {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': getCookie('csrftoken')
                        },
                        body: JSON.stringify({})
                    })
                    .then(response => {
                        if (response.ok) {
                            alert('Confirmation sent to Customer');
                            CB.disabled = true;
                            CB.textContent = 'Confirmation sent';
                        } else {
                            alert('Failed to complete order');
                        }
                        window.location.href = "/index"
                    });
                })
            })
            
        }
        let OrdersHistory = document.getElementById("OrdersHistory")
        if(OrdersHistory){
            let tabs = document.querySelectorAll(".OrdersTab")
            tabs.forEach(tab => {
                tab.addEventListener("click", function(){
                    window.location.href = "/VendorOrderDetails/" + this.dataset.order + "/" + this.dataset.user
                })
            })
        }
        let StartNav = document.querySelectorAll(".BeginNav")
        if(StartNav){
            StartNav.forEach(SN => {
                SN.addEventListener("click", function(){
                    window.location.href = "/Navi/" + this.dataset.order
                })
                
            })
        }
        let navMap = document.getElementById("NavMap")
        if(navMap){
            deliverySocket = new WebSocket('ws://' + window.location.host + '/ws/delivery/');
            deliverySocket.onopen = function(e) {
                console.log("WebSocket connection established.");
                const orderId = navMap.dataset.order; 
                initMap()
                const [ResLat, RestLng] = navMap.dataset.address.split(',').map(Number);
                console.log(ResLat, RestLng)
                let Restmarker = L.marker([ResLat, RestLng])
                .addTo(map)
                .bindPopup("Restaurant Location")
                .openPopup();
                getLocale(orderId);
            }
        }
})

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.startsWith(name + '=')) {
                cookieValue = decodeURIComponent(cookie.slice(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}


function loadOrders(id) {
    fetch('/vendor/orders/' + parseInt(id))
        .then(response => response.json())
        .then(data => {
            const ordersContainer = document.getElementById('Orders');
            ordersContainer.innerHTML = '';  

            data.forEach(order => {
                const div = document.createElement('div');
                div.classList.add('OrdersTab');
                div.innerHTML = `
                    <p>Order #${order.id}</p>
                    <p>Items: ${order.items}</p>
                    <p>Status: ${order.status}</p>
                `;
                ordersContainer.appendChild(div);
            });
        });
}


function loadNewInbox(id){
    fetch('/UpdateInbox/' + parseInt(id))
    .then(response => response.json())
    .then(data => {
        const msgContainer = document.getElementById('msgArea');
        msgContainer.innerHTML = '';  

        data.forEach(msg => {
            mli = document.createElement("li")
            mli.style = "padding: 5px 0; border-bottom: 1px solid #eee;"
            mli.innerHTML = msg.message + "<br><small>" + msg.timestamp + "</small>"
            msgContainer.appendChild(mli)
        });
    });
}


function getLocale(OrderId){
    
    navigator.geolocation.watchPosition(pos => {
        const { latitude, longitude } = pos.coords;
        const now = Date.now();
        marker.setLatLng([latitude, longitude]); //move marker
        map.setView([latitude, longitude]); //recenter map
        console.log("updated")
        if (now - lastSent > interval) {
            lastSent = now;
            const locationDisplay = document.getElementById("locationDisplay");
            locationDisplay.textContent = `Lat: ${latitude.toFixed(6)}, Lng: ${longitude.toFixed(6)}, lastUpdated: ${new Date(lastSent).toLocaleTimeString()}`;
            sendLocationToBackend(latitude, longitude, OrderId);
        }
    }, error => {
        console.error(error);
    }, {
        enableHighAccuracy: true,//more precise location
        maximumAge: 0 //always use new data and not old data from cache
    });
}

function sendLocationToBackend(lat, lang, Oid){
    if (deliverySocket.readyState === WebSocket.OPEN) {
        deliverySocket.send(JSON.stringify({
            type: 'location.update',
            latitude: lat,
            longitude: lang,
            oid: Oid
        }));
    }

}


function initMap() {
    map = L.map('NavMap').setView([0, 0], 13); //creates a map and set the initail view of the map on first creation
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors' //legally required
    }).addTo(map); //fetch the backgroud tiles from openstreetview , {z}, {x}, and {y} are placeholders for zoom level and tile coordinates.

    marker = L.marker([0, 0]).addTo(map);//set a default marker
}
