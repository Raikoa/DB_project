console.log("script.js loaded!");
let lastSent = 0; 
const interval = 5 * 1000; 
let deliverySocket;
let map;
let marker;
let routePolyline;
let fallbackPolyline;
let distanceLabel;
let lastPosition = null;
let googleMap;
let osmb;
let framenumber = 0;
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
            deliverySocket.onmessage = function(e){
                const data = JSON.parse(e.data);
                if (data.type === 'route.update') {


                        if (routePolyline) map.removeLayer(routePolyline);
                        if (fallbackPolyline) map.removeLayer(fallbackPolyline);
                        if (distanceLabel) map.removeLayer(distanceLabel);
                        if (data.route && data.route.length > 0) {
                            console.log(data.route)
                            routePolyline = L.polyline(data.route, { color: 'red' }).addTo(map);
                        }
                        if (data.fallback_line && data.fallback_line.length > 0) {
                            fallbackPolyline = L.polyline(data.fallback_line, { color: 'gray', dashArray: '5, 5' }).addTo(map);
                            const midIndex = Math.floor(data.fallback_line.length / 2);
                            const midPoint = data.fallback_line[midIndex];
                            distanceLabel = L.marker(midPoint, {
                                icon: L.divIcon({
                                    className: 'distance-label',
                                    html: `<div style="background: white; 
                                    padding: 4px 8px; 
                                    border-radius: 6px; 
                                    border: 1px solid #ccc; 
                                    font-size: 14px;
                                    font-weight: bold;
                                    box-shadow: 0 1px 5px rgba(0,0,0,0.3);
                                    white-space: nowrap;">${data.distance.toFixed(2)} km</div>`
                                })
                            }).addTo(map);
                        }
                }
            }
        }

        let addRest = document.getElementById("AddRest")
        if(addRest){
            user = addRest.getAttribute("data-user")
            addRest.addEventListener("click", function(){
                let mo = document.getElementById("RestFormModal")
                let close = document.querySelector(".close")
                if(close){
                    close.addEventListener("click", function(){
                    mo.style.display = "none"
                })
                }
                if(mo){
                    mo.style.display = "flex"
                }
                window.onclick = (e) => {
                    if (e.target == mo) {
                      mo.style.display = "none";
                    }
                  };
            })
            let RestSubmit = document.getElementById("RestSubmit")
            if(RestSubmit){
                RestSubmit.addEventListener("click", function(e){
                    e.preventDefault()
                    const form = document.getElementById("RestModalForm");
                    const formData = new FormData(form);
                    fetch("/AddRestaurant/" + parseInt(user)  , {
                        method: "POST",
                        headers: {
                            "X-CSRFToken": getCookie("csrftoken")
                        },
                        body: formData
                    })
                    .then(response => {
                        if (!response.ok) throw new Error("Network response was not ok");
                        return response.json();
                    })
                    .then(data => {
                        console.log("Success:", data);
                        alert("Restaurant added successfully!");
                        window.location.href="/index"
                    })
                    .catch(error => {
                        console.error("Error:", error);
                    });
                })
            }
        }
        let VendorMenu = document.getElementById("Menu")
        if(VendorMenu){
            VendorMenu.addEventListener("click", function(){
                window.location.href = "/Menu/" + parseInt(VendorMenu.dataset.id)
            })
        }
        let Additems = document.getElementById("AddItems")
        if(Additems){
            Rid = Additems.dataset.rid
            Additems.addEventListener("click", function(){
                let mo = document.getElementById("ItemFormModal")
                let close = document.querySelector(".close")
                if(close){
                    close.addEventListener("click", function(){
                    mo.style.display = "none"
                })
                }
                if(mo){
                    mo.style.display = "flex"
                }
                window.onclick = (e) => {
                    if (e.target == mo) {
                      mo.style.display = "none";
                    }
                  };
            })
            let ItemSubmit = document.getElementById("ItemSubmit")
            if(ItemSubmit){
                ItemSubmit.addEventListener("click", function(e){
                    e.preventDefault()
                    const form = document.getElementById("ItemModalForm");
                    const formData = new FormData(form);
                    fetch("/AddMenu/" + parseInt(Rid)  , {
                        method: "POST",
                        headers: {
                            "X-CSRFToken": getCookie("csrftoken")
                        },
                        body: formData
                    })
                    .then(response => {
                        if (!response.ok) throw new Error("Network response was not ok");
                        return response.json();
                    })
                    .then(data => {
                        console.log("Success:", data);
                        alert("Item added successfully!");
                        window.location.reload();
                    })
                    .catch(error => {
                        console.error("Error:", error);
                    });
                })
            }
        }
        let click = 1
        let manageItem = document.getElementById("ManageItems")
        if(manageItem){
            manageItem.addEventListener("click", function(){
                let btns = document.querySelectorAll(".buttonbar")
                if(btns){
                    btns.forEach(b => {

                        if(click % 2 == 0){
                            b.style.display = "None"
                        }else{
                             b.style.display = "block"
                        }

                    })
                }
                click = click + 1
            })
            let updatestatus = document.querySelectorAll(".UpdateStat")

            if(updatestatus.length > 0){
                updatestatus.forEach(u => {
                    let id = u.dataset.id

                    u.addEventListener("click", function(){
                        fetch("/UpdateMenu/" + parseInt(id)  , {
                            method: "POST",
                            headers: {
                                "X-CSRFToken": getCookie("csrftoken")
                            },
                        })
                        .then(response => {
                            if (!response.ok) throw new Error("Network response was not ok");
                            return response.json();
                        })
                        .then(data => {
                            console.log("Success:", data);
                            alert("status Changed!");
                            window.location.reload();
                        })
                        .catch(error => {
                            console.error("Error:", error);
                        });
                    })

                })
            }
            let DeleteBtn = document.querySelectorAll(".Remove")
            if(DeleteBtn.length > 0){
                DeleteBtn.forEach(d => {
                    let id = d.dataset.id
                    d.addEventListener("click", function(){
                        fetch("/DeleteMenu/" + parseInt(id)  , {
                            method: "POST",
                            headers: {
                                "X-CSRFToken": getCookie("csrftoken")
                            },
                        })
                        .then(response => {
                            if (!response.ok) throw new Error("Network response was not ok");
                            return response.json();
                        })
                        .then(data => {
                            console.log("Success:", data);
                            alert("Item deleted!");
                            window.location.reload();
                        })
                        .catch(error => {
                            console.error("Error:", error);
                        });
                    })
                })
            }

        }
        let ShowUserOrder = document.getElementById("UserCurrentOrder")

            if(ShowUserOrder){
                ShowUserOrder.addEventListener("click", function(){
                    window.location.href = "/ShowUserCurrentOrder/" + parseInt(ShowUserOrder.dataset.user)
                })
            }
            let tracker = document.querySelectorAll(".trackBtn")
            if(tracker.length > 0){
                tracker.forEach(track => {
                    track.addEventListener("click", function(){

                        let orderid = track.dataset.id
                        window.location.href = "/Tracker/" + parseInt(orderid)

                    })
                })
            }
            let ShowUserCurrentItem = document.querySelectorAll(".ShowCurrentOrderUserItems")
            if(ShowUserCurrentItem.length > 0){
                let mo = document.querySelector("#UserOrderModal")
                let co = document.querySelector("#UserOrdermodalContent")
                let close = mo.querySelector(".close");
            if(close){

                close.addEventListener("click", function(){

                mo.style.display = "none"
            })
            }

            ShowUserCurrentItem.forEach(Mod => {
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
            let trackerImage = document.getElementById("trackerImage")
            if(trackerImage){
                let orderid = trackerImage.dataset.order
                let socket = new WebSocket("ws://" + window.location.host + "/ws/map/");
                console.log("socket connected")
                        socket.onmessage = function(e) {
                            const data = JSON.parse(e.data);
                            if (data.type === "error") {
                                alert(data.message);
                            } else if (data.type === "map") {

                                console.log(data.lat)
                                console.log(data.lng)
                                trackerImage.setAttribute("data-lat", data.lat)
                                trackerImage.setAttribute("data-lng", data.lng)

                                osmb = new OSMBuildings({
                                    container: 'trackerImage',
                                    position: { latitude: parseFloat(data.lat), longitude: parseFloat(data.lng) },
                                    zoom: 17,
                                    minZoom: 15,
                                    maxZoom: 20,
                                    state: true,
                                    tilt: 40,
                                    rotation: 300,
                                    effects: ['shadows'],
                                    tileSource: 'https://a.tile.openstreetmap.org/{z}/{x}/{y}.png',
                                    attribution: '© Data <a href="https://openstreetmap.org/copyright/">OpenStreetMap</a> © Map <a href="https://osmbuildings.org/copyright/">OSM Buildings</a>'
                                });
                                osmb.addMapTiles('https://tile-a.openstreetmap.fr/hot/{z}/{x}/{y}.png');

                                osmb.addGeoJSONTiles('https://{s}.data.osmbuildings.org/0.2/59fcc2e8/tile/{z}/{x}/{y}.json');
                                const pos = osmb.project([lng, lat]);
                                const marker = document.getElementById('3Dmarker');
                                if (pos) {
                                marker.style.left = pos.x + 'px';
                                marker.style.top = pos.y + 'px';
                                }
                                let rotation = 300;
                                setInterval(() => {
                                rotation = (rotation + 1) % 360;
                                osmb.setRotation(rotation);
                                }, 100);

                            }
                        };
                        socket.onopen = function() {
                            console.log("socket sent")
                            socket.send(JSON.stringify({
                                type: "request_map",
                                order_id: orderid
                            }));
                        };
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

/*
function getLocale(OrderId){
    
    navigator.geolocation.watchPosition(pos => {
        const { latitude, longitude } = pos.coords;
        const now = Date.now();
        marker.setLatLng([latitude, longitude]); //move marker
        map.setView([latitude, longitude]); //recenter map

        if (now - lastSent > interval) {
            lastSent = now;
            console.log("updated")
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
    navigator.geolocation.getCurrentPosition(pos => {
        const { latitude, longitude } = pos.coords;
        const now = Date.now();
        marker.setLatLng([latitude, longitude]);
        map.setView([latitude, longitude]);
        console.log("getCurrentPosition update");

        const locationDisplay = document.getElementById("locationDisplay");
        locationDisplay.textContent = `Lat: ${latitude.toFixed(6)}, Lng: ${longitude.toFixed(6)}, lastUpdated: ${new Date(now).toLocaleTimeString()}`;
        sendLocationToBackend(latitude, longitude, OrderId);
        lastSent = now;
    }, error => {
        console.error("getCurrentPosition error", error);
    }, {
        enableHighAccuracy: true,
        timeout: 15000
    });
    setInterval(() => {
        navigator.geolocation.getCurrentPosition(pos => {
            const { latitude, longitude } = pos.coords;
            const now = Date.now();
            marker.setLatLng([latitude, longitude]);
            map.setView([latitude, longitude]);
            console.log("Forced getCurrentPosition update");

            const locationDisplay = document.getElementById("locationDisplay");
            locationDisplay.textContent = `Lat: ${latitude.toFixed(6)}, Lng: ${longitude.toFixed(6)}, lastUpdated: ${new Date(now).toLocaleTimeString()}`;
            sendLocationToBackend(latitude, longitude, OrderId);
            lastSent = now;
        }, error => {
            console.error("getCurrentPosition error", error);
        }, {
            enableHighAccuracy: true,
            timeout: 15000
        });
    }, 30000);
}
*/

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

function getDistance(lat1, lon1, lat2, lon2) {
    const R = 6371e3;
    const toRad = angle => angle * Math.PI / 180;
    const dLat = toRad(lat2 - lat1);
    const dLon = toRad(lon2 - lon1);
    const a = Math.sin(dLat / 2) ** 2 +
              Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) *
              Math.sin(dLon / 2) ** 2;
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
}

function isRedundant(pos) {
    if (!lastPosition) return false;
    const { latitude, longitude } = pos.coords;
    const { latitude: lastLat, longitude: lastLng } = lastPosition.coords;
    const distance = getDistance(latitude, longitude, lastLat, lastLng);
    return distance < 10;
}

function handleLocation(pos, OrderId) {
    const now = Date.now();

    if (isRedundant(pos)) {
        console.log(" Ignoring redundant update");
        return;
    }

    const { latitude, longitude, accuracy } = pos.coords;
    if (accuracy > 50) {
        console.log(" Skipping due to poor accuracy:", accuracy);
        return;
    }

    lastPosition = pos;
    lastSent = now;

    marker.setLatLng([latitude, longitude]);
    map.setView([latitude, longitude]);

    const locationDisplay = document.getElementById("locationDisplay");
    locationDisplay.textContent = `Lat: ${latitude.toFixed(6)}, Lng: ${longitude.toFixed(6)}, Accuracy: ${accuracy.toFixed(1)}m, Time: ${new Date(now).toLocaleTimeString()}`;
    SaveFrame(OrderId, latitude, longitude, framenumber)
    framenumber = framenumber + 1
    sendLocationToBackend(latitude, longitude, OrderId);
}

function getLocale(OrderId) {
    navigator.geolocation.getCurrentPosition(pos => {
        console.log(" Initial location fix");
        handleLocation(pos, OrderId);
    }, error => {
        console.error("getCurrentPosition error", error);
    }, {
        enableHighAccuracy: true,
        timeout: 15000
    });

    setInterval(() => {
        navigator.geolocation.getCurrentPosition(pos => {
            console.log("Periodic location request");
            handleLocation(pos, OrderId);
        }, error => {
            console.error("getCurrentPosition error", error);
        }, {
            enableHighAccuracy: true,
            timeout: 15000
        });
    }, 30000);
}


function initStreetView(){
    const lat = parseFloat(document.getElementById("trackerImage").dataset.lat);
    const lng = parseFloat(document.getElementById("trackerImage").dataset.lng);

    const location = { lat, lng };


    const panorama = new google.maps.StreetViewPanorama(
        document.getElementById("street-view"),
        {
            position: location,
            pov: {
                heading: 34,
                pitch: 10
            },
            zoom: 1
        }
    );


}


function SaveFrame(Oid, lat,lng, FrameNum){
    if (deliverySocket.readyState === WebSocket.OPEN) {
        deliverySocket.send(JSON.stringify({
            type: 'frameRequest',
            latitude: lat,
            longitude: lng,
            oid: Oid,
            FrameNumber: FrameNum
        }));
    }
}
/*
function initGoogleMap() {
    const lat = parseFloat(document.getElementById("trackerImage").dataset.lat);
    const lng = parseFloat(document.getElementById("trackerImage").dataset.lng);
    googleMap = new google.maps.Map(document.getElementById("Googlemap"), {
      center: { lat: lat, lng: lng },
      zoom: 18,
      heading: 320,
      tilt: 45, // required for 3D buildings
      mapId: "8e0a97af9386fef", // default mapId with 3D support
      mapTypeId: 'roadmap',
      disableDefaultUI: false,
    });

    // Optional: animate rotation
    let heading = 320;
    setInterval(() => {
      heading += 1;
      map.setHeading(heading);
    }, 100);
  }*/
/*
    function initAllMaps() {
        const tracker = document.getElementById("trackerImage");
        const lat = parseFloat(tracker.dataset.lat);
        const lng = parseFloat(tracker.dataset.lng);
        const location = { lat, lng };

        const panorama = new google.maps.StreetViewPanorama(
            document.getElementById("street-view"),
            {
                position: location,
                pov: {
                    heading: 34,
                    pitch: 10
                },
                zoom: 1
            }
        );


        const googleMap = new google.maps.Map(document.getElementById("Googlemap"), {
            center: location,
            zoom: 18,
            heading: 320,
            tilt: 45,
            mapId: "8e0a97af9386fef",
            mapTypeId: 'roadmap'
        });


        let heading = 320;
        setInterval(() => {
            heading = (heading + 1) % 360;
            googleMap.setHeading(heading);
        }, 100);
    }*/


