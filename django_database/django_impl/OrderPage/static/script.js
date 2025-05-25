console.log("script.js loaded!");
let lastSent = 0; 
const interval = 5 * 1000; 
let deliverySocket;
let map;
let marker;
let routePolyline;
let routeStaticPolyLine;
let fallbackPolyline;
let distanceLabel;
let lastPosition = null;
let googleMap;
let osmb;
let framenumber = 0;
let heatLayer;
let heatmap
let coloredSegments = [];
let isGoogleMapsLoaded = false;
let latLng = null;
let city
let Predmarker
let RestPredMarker
let have_dest = false
document.addEventListener("DOMContentLoaded", function(){
        
        let tabs = document.querySelectorAll(".restaurant_tab")
        if(tabs.length > 0){
            let userid = document.getElementById("Menus").dataset.user
            loadNewInbox(userid)
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
        let mails = document.getElementById("Mails")
        if(mails){
            console.log("in mail")
            let ms = document.querySelectorAll(".msgTab")
            if(ms.length > 0){
                console.log(ms.length)
                const orderPattern = /#(\d+)#/;
                ms.forEach(m => {
                    console.log("matching")
                    let match = m.innerText.match(orderPattern);
                    console.log(match)
                    if(match){
                        id = mails.dataset.id
                        let orderId = match[1];
                        fetch('/CheckAlreadyReviewed/' + orderId, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': getCookie('csrftoken')
                        },
                            body: JSON.stringify({})
                        })
                        .then(response => {
                            if (!response.ok) {
                                throw new Error('Network response was not ok');
                            }
                            return response.json();
                        })
                        .then(data => {
                            if (data.Valid) {
                                const rateBtn = document.createElement("button");
                                rateBtn.textContent = "Rate Order #" + orderId;
                                rateBtn.className = "rate-button"; 
                                rateBtn.id = "rate_" + orderId
                                rateBtn.onclick = function() {
                                    window.location.href = "/rateOrder/" + orderId + "/" + id;
                                };
                                m.appendChild(rateBtn);
                                
                            }
                        })
                        .catch(error => {
                            console.error('Fetch error:', error);
                        });
                        
                    }
                })
            }
            let search = document.getElementById("InboxSearchBtn")
            if(search){
                search.addEventListener("click", function(){
                    let SearchQuery = document.getElementById("InboxSearch").value
                    id = mails.dataset.id
                    if(SearchQuery){
                        fetch('/GetInbox/' + id, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': getCookie('csrftoken')
                        },
                        body: JSON.stringify({
                            query: SearchQuery
                        })
                    })
                    .then(response => {
                        if (!response.ok) {
                            throw new Error('Network response was not ok');
                        }
                        return response.json();
                    })
                    .then(data => {
                        if(data.messages && data.messages.length > 0){
                                let mo = document.querySelector("#ResultInboxModal")
                                let co = document.querySelector("#ResultInboxModalContent")
                                let close = mo.querySelector(".close")
                                if(close){
                                    close.addEventListener("click", function(){
                                        mo.style.display = "none"
                                    })
                                }
                                co.innerHTML = ""; 

                                data.messages.forEach(me => {
                                let msgDiv = document.createElement("div");
                                msgDiv.className = "inbox-message";
                                msgDiv.innerHTML = `
                                    <div class="msg-box" style="border-bottom: 1px solid #ccc; padding: 10px;">
                                        <p><strong>Message:</strong> ${me.message}</p>
                                        <p><small><strong>Time:</strong> ${me.timestamp}</small></p>
                                    </div>
                                `;
                                co.appendChild(msgDiv);
                            });
                                mo.style.display = "flex"
                            }else{
                                alert("No messages found.");
                            }
                                })
                                .catch(error => {
                                    console.error('Fetch error:', error);
                                });
                                window.onclick = (e) => {
                                    if (e.target == mo) {
                                    mo.style.display = "none";
                                    }
                                };
                        }
                })
            }
            let delMsg = document.querySelectorAll(".DeleteMsg")
            console.log(delMsg)
            if(delMsg.length > 0){
                delMsg.forEach( d => {
                    d.addEventListener("click", function(){
                        msgID = d.dataset.id
                        fetch('/DeleteInbox/' + parseInt(msgID), {
                        method: 'POST',
                        headers: {
                            'X-CSRFToken': getCookie('csrftoken'),
                        }
                    })
                    .then(response => {
                        if (!response.ok) throw new Error("Failed to delete restaurant");
                        return response.json();
                    })
                    .then(data => {
                        if (data.status === "success") {
                            alert("Inbox deleted successfully");
                            window.location.reload();
                        } else {
                            alert("Error deleting restaurant");
                            console.error(data);
                        }
                    })
                    .catch(err => {
                        console.error(err);
                        alert("Something went wrong.");
                    });
                    })
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
            let close = mo.querySelector(".close")
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
        let estimate = document.getElementById("DeliveryEstimate")
        if(estimate){
            estimate.addEventListener("click", function(){
                window.location.href = "/DeliveryEstimate/"
            })
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
            let difficulty = document.querySelectorAll(".difficulty")
            if(difficulty.length > 0){
                difficulty.forEach( d => {
                    d.addEventListener("click", function(){
                        Oid = d.dataset.oid
                        //get the city the order destination and the restaurant is in 
                        fetch('/GetCity/' + Oid, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': getCookie('csrftoken')
                        },
                        body: JSON.stringify({})
                    })
                    .then(response => {
                        if (!response.ok) {
                            throw new Error('Network response was not ok');
                        }
                        return response.json();
                    })
                    .then(data => {
                        if (data.status === 'success') {
                            city = data.city;
                            window.location.href = "/AreaEstimateDeli/" + city + "/" + Oid
                            console.log('City:', city);
                            
                        } else {
                            console.error('Server error:', data);
                        }
                    })
                    .catch(error => {
                        console.error('Fetch error:', error);
                    });
                       
                    })
                })
            }
        }

        let button = document.getElementById('TakeOrderBtn');
        if(button){
            const protocol = window.location.protocol === "https:" ? "wss://" : "ws://";
            const socket = new WebSocket(protocol + window.location.host + "/ws/Heatmap/");
            console.log("socket connected")
            socket.onopen = function(e) {
                socket.send(JSON.stringify({
                        "type": "UpdateDiff",
                        "Dest_address": document.getElementById("Dest_addr").innerText,
                        "Rest_address": document.getElementById("Rest_addr").innerText,
                        "Oid": document.getElementById("DetailOrderId").innerText,
                    }));
            }
            socket.onmessage = function(e) {
                const data = JSON.parse(e.data);
                console.log('Update received:', data.stat);
            };
            
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
        if(completeDelivery.length > 0){
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
                const [DestLat, DestLng] = navMap.dataset.dest.split(',').map(Number);
                console.log(ResLat, RestLng)
                let Restmarker = L.marker([ResLat, RestLng])
                .addTo(map)
                .bindPopup("Restaurant Location")
                
                console.log(DestLat, DestLng)
                let destMarker = L.marker([DestLat, DestLng]).addTo(map).bindPopup("Customer Destination");
                getLocale(orderId);
            }
            deliverySocket.onmessage = function(e){
                const data = JSON.parse(e.data);
                if (data.type === 'route.update') {


                        if (routePolyline) map.removeLayer(routePolyline);
                        if (fallbackPolyline) map.removeLayer(fallbackPolyline);
                        if (distanceLabel) map.removeLayer(distanceLabel);
                        if (routeStaticPolyLine) map.removeLayer(routeStaticPolyLine);
                        if (data.route && data.route.length > 0) {
                            console.log(data.route)
                            routePolyline = L.polyline(data.route, { color: 'red' }).addTo(map);
                        }
                        if(data.static_route && data.static_route.length > 0){
                            console.log(data.static_route)
                            routeStaticPolyLine = L.polyline(data.static_route, { color: 'Blue' }).addTo(map);
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
              
                
                if (data.type == "heatmap_data"){
                    initHeatMap();
                    if (coloredSegments) {
                    coloredSegments.forEach(seg => heatmap.removeLayer(seg));
                    }
                    coloredSegments = [];
                   

                for (let i = 0; i < data.heatmap.length - 1; i++) {
                    const p1 = data.heatmap[i];
                    const p2 = data.heatmap[i + 1];
                    const score = (p1.score + p2.score) / 2;
                    console.log(score)
                    const color = getColorForScore(score);
                    const segment = L.polyline([[p1.lat, p1.lng], [p2.lat, p2.lng]], {
                        color: color,
                        weight: 8,
                        opacity: 0.9,
                        smoothFactor: 1
                    }).addTo(heatmap);

                    coloredSegments.push(segment);

                }
                const bounds = L.latLngBounds(data.heatmap.map(p => [p.lat, p.lng]));
                heatmap.fitBounds(bounds);

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


            let EditBtn = document.querySelectorAll(".EditItem")
          
            if(EditBtn.length > 0){
                EditBtn.forEach(E => {
                     
                    E.addEventListener("click", function(){
                        selectedId = E.dataset.id
                        let mo = document.getElementById("ItemFormUpdateModal")
                        let close = document.querySelector(".close")
                        if(close){
                        close.addEventListener("click", function(){
                        mo.style.display = "none"
                    })
                    }
                    if(mo){
                        mo.style.display = "flex"
                        document.getElementById("updateName").value = document.getElementById("name_" + selectedId).innerText
                        document.getElementById("updatePrice").value = document.getElementById("price_" + selectedId).innerText
                        document.getElementById("currentPicPreview").src = document.getElementById("pic_" + selectedId).src;
                        document.getElementById("updateDesc").value = document.getElementById("tab_" + selectedId).dataset.desc
                    }
                    window.onclick = (e) => {
                        if (e.target == mo) {
                         mo.style.display = "none";
                        }   
                    };
                    })
                })
                let UpdateSubmit = document.getElementById("UpdateSubmit")
                if(UpdateSubmit){
                    UpdateSubmit.addEventListener("click", function(e){
                        e.preventDefault()
                        const form = document.getElementById("ItemModalUpdateForm");
                        const formData = new FormData(form);
                        fetch("/EditMenu/" + parseInt(selectedId)  , {
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
                        alert("Item Edited successfully!");
                        window.location.reload();
                        })
                        .catch(error => {
                        console.error("Error:", error);
                        });
                    })
                }
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
                                updateLatLng(data.lat, data.lng);
                                osmb = new OSMBuildings({
                                    container: 'trackerImage',
                                    position: { latitude: parseFloat(data.lat), longitude: parseFloat(data.lng) },
                                    zoom: 17,
                                    minZoom: 17,
                                    maxZoom: 17,
                                    state: true,
                                    tilt: 40,
                                    rotation: 300,
                                    effects: ['shadows'],
                                    state: false,
                                    controls: false,
                                    tileSource: 'https://a.tile.openstreetmap.org/{z}/{x}/{y}.png',
                                    attribution: '© Data <a href="https://openstreetmap.org/copyright/">OpenStreetMap</a> © Map <a href="https://osmbuildings.org/copyright/">OSM Buildings</a>'
                                });
                                osmb.addMapTiles('https://tile-a.openstreetmap.fr/hot/{z}/{x}/{y}.png');

                                osmb.addGeoJSONTiles('https://{s}.data.osmbuildings.org/0.2/59fcc2e8/tile/{z}/{x}/{y}.json');
                                setTimeout(() => {
                                    /*const pos = osmb.project([parseFloat(data.lng), parseFloat(data.lat)]);
                                    const marker = document.getElementById('3Dmarker');
                                    if (pos) {
                                        console.log("Projected position:", pos);
                                        marker.style.left = `${pos.x}px`;
                                        marker.style.top = `${pos.y}px`;
                                    }
                                    */
                                
                              
                                 let rotation = 300;
                                    setInterval(() => {
                                    rotation = (rotation + 1) % 360;
                                    osmb.setRotation(rotation);
                                    }, 300);
                                    }, 3000);
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
            let searchbtn = document.getElementById("Search")
            if(searchbtn){
                searchbtn.addEventListener("click", function(){
                    const form = document.getElementById("searchbar");
                    
                    const formData = new FormData(form);
                    const searchValue = formData.get("search");
                    fetch("/SearchMenu"  , {
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
                        document.getElementById("SearchModal").style.display = "flex"
                        let s = document.getElementById("searchResult")
                    
                        s.innerText = data.name + ":" + data.price
                        window.onclick = (e) => {
                            if (e.target == document.getElementById("SearchModal")) {
                                document.getElementById("SearchModal").style.display = "none";
                            }
                          };
                        })
                        .catch(error => {
                        console.error("Error:", error);
                        });
                })
            }
            let regions = document.querySelectorAll(".region-label")
            if(regions){
                regions.forEach(re =>{
                    re.addEventListener("click", function(){
                        window.location.href = "/AreaEstimate/" + re.dataset.region
                    })
                })
            }
            let subHeat = document.getElementById("SubmitHeat")
            if(subHeat){
                const Predictmap = L.map('heatmapMap', {
                    zoomControl: false,
                    scrollWheelZoom: false,
                    doubleClickZoom: false,
                    boxZoom: false,
                    touchZoom: false,
                    dragging: false, // Optional: also disables dragging
                }).setView([25.0330, 121.5654], 10);
                L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                    attribution: 'Map data © OpenStreetMap contributors'
                }).addTo(Predictmap);
              
                let data_dest = document.getElementById("Dest_data")
                let dest_lat = null
                let dest_lng = null
                let data_Rest = document.getElementById("Rest_data")
                let rest_lat = null
                let rest_lng = null
                if(data_Rest){
                    rest_lat = data_Rest.dataset.lat
                    rest_lng = data_Rest.dataset.lng
                    RestPredMarker = L.marker([rest_lat, rest_lng])
                    .addTo(Predictmap)
                    .bindPopup("restaurant Location")
                   
                }
                if(data_dest){
                    console.log("got data_dest")
                    dest_lat = data_dest.dataset.lat
                    dest_lng = data_dest.dataset.lng
                     Predmarker = L.marker([dest_lat, dest_lng])
                    .addTo(Predictmap)
                    .bindPopup("Destination Location")
                  
                    Predictmap.setView(Predmarker.getLatLng(), 11);
                    have_dest = true
                    document.getElementById("weatherControl").style.display = "none"
                    
                    
                }
                
                let heatLayer = null;
                const protocol = window.location.protocol === "https:" ? "wss://" : "ws://";
                const socket = new WebSocket(protocol + window.location.host + "/ws/Heatmap/");
                console.log("socket connected")
                
                subHeat.addEventListener("click", function(){
                    subHeat.disabled = true;
                    oid = subHeat.dataset.oid
                    weekday = document.getElementById("weekDays").value
                    time = document.getElementById("timeOfDay").value
                    //weather = document.getElementById("weather").value
                    if(rest_lat != null && dest_lat != null){
                        socket.send(JSON.stringify({
                        "type": "Prediction_info",
                        "weekday": weekday,
                        "time": time,
                        //"weather": weather,
                        // "temp": parseFloat(document.getElementById("temp").value),
                        // "rain": parseFloat(document.getElementById("rain").value),
                        // "wind_speed": parseFloat(document.getElementById("wind_speed").value),
                        // "visibility": parseInt(document.getElementById("visibility").value),
                        // "thunder": document.getElementById("thunder").checked,
                        "city": document.getElementById("Area").dataset.city,
                        "dest_node": dest_lat + ":" + dest_lng,
                        "rest_node": rest_lat + ":" + rest_lng,
                        "oid": oid
                    }));
                    }else{
                        socket.send(JSON.stringify({
                        "type": "Prediction_info",
                        "weekday": weekday,
                        "time": time,
                        //"weather": weather,
                        "temp": parseFloat(document.getElementById("temp").value),
                        "rain": parseFloat(document.getElementById("rain").value),
                        "wind_speed": parseFloat(document.getElementById("wind_speed").value),
                        "visibility": parseInt(document.getElementById("visibility").value),
                        "thunder": document.getElementById("thunder").checked,
                        "city": document.getElementById("Area").dataset.city,
                        
                    }));
                    }
                    

                    
                })
                socket.onmessage = function(e) {
                            console.log("[WS] Message received!");
                            const data = JSON.parse(e.data);
                            console.log(data)
                            if (data.type === "HeatMap") {
                                console.log("heatmap received:", data);

                                // Convert heatmap data to [lat, lng, intensity]
                                const points = data.heatmap.map(p => [p.lat, p.lng, p.value]);

                                // Remove old heat layer if exists
                                if (heatLayer) {
                                    Predictmap.removeLayer(heatLayer);
                                }

                                // Create and add new heat layer
                                heatLayer = L.heatLayer(points, {
                                    radius: 20,
                                    blur: 15,
                                    maxZoom: 17,
                                    minOpacity: 0.5,
                                    max: 60,
                                    min: 10,
                                }).addTo(Predictmap);
                
                            }
                            if (data.bounds && data.bounds.sw && data.bounds.ne) {
                            const bounds = L.latLngBounds(
                                [data.bounds.sw.lat, data.bounds.sw.lng],
                                [data.bounds.ne.lat, data.bounds.ne.lng]
                            );
                            Predictmap.fitBounds(bounds);
                            // // Check if marker exists
                            // if (typeof Predmarker !== "undefined" && Predmarker) {
                            //     // Focus on the marker with a suitable zoom level
                            //     Predictmap.setView(Predmarker.getLatLng(), 15);
                            // } else {
                            //     // Otherwise, fit to heatmap bounds
                            //     Predictmap.fitBounds(bounds);
                            // }
                            }
                            if(data.Rest_score && data.Dest_score){
                                let avg = (data.Rest_score + data.Dest_score)
                                diff = document.getElementById("difficulties")
                                if(avg <= 0.5){
                                    diff.innerText = "Easy"
                                    
                                }else if(avg <= 1 && avg > 0.5){
                                    diff.innerText = "Normal"
                                }else if(avg <= 1.5 && avg > 1){
                                    diff.innerText = "Expert"
                                }else{
                                    diff.innerText = "Hard"
                                }
                            }
                    };
            }
            Ratings = document.getElementById("SubmitRating")
            if(Ratings){
                oid = Ratings.dataset.oid
                uid = Ratings.dataset.uid
                Ratings.addEventListener("click", function(){
                    score = document.getElementById("score").value
                    comment = document.getElementById("comment").value
                    fetch("/ProcessOrder/" + oid + "/" + parseInt(score) + "/" + comment, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': getCookie('csrftoken')
                        },
                        body: JSON.stringify({})
                    })
                    .then(response => {
                        if (!response.ok) {
                            throw new Error('Network response was not ok');
                        }
                        return response.json();
                    })
                    .then(data => {
                        if (data.status === 'success') {
                            alert("Thanks for the review")
                           console.log("successfully Review")
                            
                        } else {
                            console.error('Error:', data);
                        }
                        window.location.href = "/Inbox/" + uid
                    })
                    .catch(error => {
                        console.error('Fetch error:', error);
                    });
                })
                
                

            }
            let rank = document.getElementById("Rankings")
            if(rank){
                uid = rank.dataset.id 
                rank.addEventListener("click", function(){
                    window.location.href = "/Rankings/"
                })
            }
            let SearchRestaurant = document.getElementById("SearchRestaurant")
            if(SearchRestaurant){
                let mo = document.querySelector("#SearchModal")
                let co = document.querySelector("#SearchModalContent")
                let close = mo.querySelector(".close");
                if(close){

                    close.addEventListener("click", function(){

                    mo.style.display = "none"
                })
                }

                
                SearchRestaurant.addEventListener("click", function(){
             
               
                mo.style.display = "flex"
                let but = document.getElementById("SearchWithTags")
                if(but){
                    but.addEventListener("click", function () {
                    let name = document.getElementById("Restaname").value;

                    // Get checked tag checkboxes
                    let checkedBoxes = document.querySelectorAll('input[name="tagsSearch"]:checked');
                    let selectedTagIds = Array.from(checkedBoxes).map(cb => parseInt(cb.value));

                    // Send POST request with both name and tag IDs
                    fetch('/SearchRestaurantsWithTag/', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': getCookie('csrftoken')
                        },
                        body: JSON.stringify({
                            name: name,
                            tags: selectedTagIds
                        })
                    })
                    .then(response => {
                        if (!response.ok) {
                            throw new Error('Network response was not ok');
                        }
                        return response.json();
                    })
                    .then(data => {
                             if (data.restaurants && data.restaurants.length > 0) {
                                    let mo2 = document.querySelector("#ResultModal")
                                    let co2 = document.querySelector("#ResultModalContent")
                                    let close = mo2.querySelector(".close");
                                    co2.innerHTML = "";
                                    if(close){

                                        close.addEventListener("click", function(){

                                        mo2.style.display = "none"
                                    })
                                    }
                                     const menusDiv = document.createElement("div");
                                        menusDiv.id = "Menus";
                                        menusDiv.dataset.user = but.dataset.userid;


                                    data.restaurants.forEach(restaurant => {
                                        const restDiv = document.createElement("div");
                                        restDiv.className = "restaurant_tab";
                                        restDiv.setAttribute("data-id", restaurant.id);

                                        restDiv.innerHTML = `
                                            <img src="${restaurant.picture}" class="display" alt="${restaurant.name}" />
                                            <p>${restaurant.name}</p>
                                        `;

                                        
                                        restDiv.addEventListener("click", () => {
                                            window.location.href = "/pages/" + restaurant.id +"/"
                                          
                                        });

                                        menusDiv.appendChild(restDiv);
                                    });
                                     co2.appendChild(menusDiv);
                                     mo2.style.display = "flex"
                                     
                                     window.onclick = (e) => {
                                    if (e.target == mo) {
                                    mo2.style.display = "none";
                                    }
                                    };
                             }else{
                                 alert("No restaurants found with that search.");
                             }
                    })
                    .catch(error => {
                        console.error('Fetch error:', error);
                    });
                });

                }
              
                window.onclick = (e) => {
                if (e.target == mo) {
                mo.style.display = "none";
                }
                };
                    
            })
            }
            let account = document.getElementById("Account")
            if(account){
                console.log(account.dataset.userid)
                console.log(account.dataset.role)
                account.addEventListener("click", function(){
                    window.location.href = "/AccountInfo/" + parseInt(account.dataset.userid) + "/" + account.dataset.role
                })
            }
            let upd = document.getElementById("UpdateInfo")
            if(upd){
                upd.addEventListener("click", function (e) {
                    e.preventDefault(); 

                    const form = document.getElementById("UpdateAccountForm");
                    const formData = new FormData(form);

                    
                    // let data = {};
                    // for (let [key, value] of formData.entries()) {
                    //     data[key] = value;
                    // }

                    // console.log(data); 
                    userid = document.getElementById("AccountDetails").dataset.userid
                    role = document.getElementById("AccountDetails").dataset.role
                    fetch("/UpdateAccountInfo/" + parseInt(userid) + "/" + role, {
                            method: 'POST',
                            headers: {
                                'X-CSRFToken': getCookie('csrftoken')  
                            },
                            body: formData
                        })
                        .then(response => {
                            if (!response.ok) throw new Error('Network response was not ok');
                            return response.json();
                        })
                        .then(data => {
                            if (data.status === 'success') {
                                alert("Account Updated");
                            } else {
                                console.error('Error:', data);
                            }
                            window.location.href = "/index";
                        });
                    });
            }
            let deleteRest = document.getElementById("DeleteRestaurant")
            if(deleteRest){
                deleteRest.addEventListener("click", function(){
                    userid = deleteRest.dataset.user
                    Rid = deleteRest.dataset.restaurant
                    const confirmed = window.confirm("Are you sure you want to delete this restaurant? This action cannot be undone.");
                     if (confirmed) {
                    
                    fetch(`/DeleteRestaurant/${parseInt(userid)}/${parseInt(Rid)}/`, {
                        method: 'POST',
                        headers: {
                            'X-CSRFToken': getCookie('csrftoken'),
                        }
                    })
                    .then(response => {
                        if (!response.ok) throw new Error("Failed to delete restaurant");
                        return response.json();
                    })
                    .then(data => {
                        if (data.status === "success") {
                            alert("Restaurant deleted successfully");
                            window.location.href = "index/";
                        } else {
                            alert("Error deleting restaurant");
                            console.error(data);
                        }
                    })
                    .catch(err => {
                        console.error(err);
                        alert("Something went wrong.");
                    });
                }
                })
            }
           let Datesearch = document.getElementById("searchBtnDate");

if (Datesearch) {
    Datesearch.addEventListener("click", function () {
        const searchDate = document.getElementById("searchDateInput").value;
        const userid = Datesearch.dataset.user;

        if (!searchDate) {
            alert("Please select a date.");
            return;
        }

        fetch("/GetOrderByDate/" + searchDate + "/" + parseInt(userid), {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCookie("csrftoken")
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error("Network response was not ok");
            }
            return response.json();
        })
        .then(data => {
            if (data.status === "success") {
                const orders = data.Result;
                const modal = document.getElementById("DateModal");
                const modalContent = document.getElementById("DatemodalContent");
                let close = modal.querySelector(".close")
                if(close){
                    close.addEventListener("click", function(){
                    modal.style.display = "none"
                    })
                }
                window.onclick = (e) => {
                    if (e.target == modal) {
                        modal.style.display = "none";
                    }
                };
                modalContent.innerHTML = ""; 

                if (orders.length === 0) {
                    modalContent.innerHTML = "<p>No orders found for selected date.</p>";
                } else {
                    orders.forEach(i => {
                        modalContent.innerHTML += `
                        <div class="Orderstab">
                            <p><strong>Order ID:</strong> ${i.id}</p>
                            <p><strong>Created:</strong> ${i.created}</p>
                            <p><strong>Completed:</strong> ${i.completed}</p>
                            <p><strong>Delivery Person:</strong> ${i.delivery_person_name}</p>
                            <p><strong>Restaurant:</strong> ${i.restaurant}</p>
                            <p><strong>Destination:</strong> ${i.destination}</p>
                            <p><strong>Price:</strong> ${i.price}</p>
                            <p><strong>Status:</strong> ${i.status}</p>
                            <p><strong>Items:</strong></p>
                            <ul>
                                ${JSON.parse(i.items).map(item => `
                                    <li>${item.name} - $${item.price}<br><em>${item.desc}</em></li>
                                `).join("")}
                            </ul>
                            <hr>
                        </div>`;
                    });
                }

                modal.style.display = "flex"; 
            } else {
                console.error("Error fetching orders:", data.message);
            }
            })
            .catch(error => {
                    console.error("Fetch error:", error);
                });
            });
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
        const orderPattern = /#(\d+)#/;
        data.forEach(msg => {
            mli = document.createElement("li")
            mli.style = "padding: 5px 0; border-bottom: 1px solid #eee;"
            mli.innerHTML = msg.message + "<br><small>" + msg.timestamp + "</small>"
            const match = msg.message.match(orderPattern);
            console.log(match)
            if (match) {
                const orderId = match[1];
                const rateBtn = document.createElement("button");
                rateBtn.textContent = "Rate Order #" + orderId;
                rateBtn.className = "rate-button"; 
                rateBtn.id = "rate_" + orderId
                if (msg.reviewed) {
                    rateBtn.disabled = true;
                    rateBtn.textContent += " (Reviewed)";
                    rateBtn.style.opacity = 0.6;
                    rateBtn.style.cursor = "not-allowed";
                } else {
                    rateBtn.onclick = function () {
                        window.location.href = "/rateOrder/" + orderId + "/" + id;
                    };
                }

                mli.appendChild(document.createElement("br"));
                mli.appendChild(rateBtn);
            }
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
    console.log(distance)
    return distance < 5;
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
    //SaveFrame(OrderId, latitude, longitude, framenumber)
    //framenumber = framenumber + 1
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


function initStreetView() {
    const orderId = document.getElementById("trackerImage").dataset.order;

    fetch('/GetCurrentCoords/' + orderId, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === "success") {
            const lat = parseFloat(data.lat);
            const lng = parseFloat(data.lng);
            const location = { lat, lng };

            console.log("Street View location:", location);
            const streetViewService = new google.maps.StreetViewService();
            streetViewService.getPanorama({
            location: location,
            radius: 100 
            }, (data, status) => {
            if (status === google.maps.StreetViewStatus.OK) {
            const panorama = new google.maps.StreetViewPanorama(
            document.getElementById("street-view"),
            {
                pano: data.location.pano,
                pov: {
                    heading: 34,
                    pitch: 10
                },
                zoom: 1
            }
        );
    } else {
        console.warn("No Street View available:", status);
        document.getElementById("street-view").innerHTML = "<p>No Street View available at this location.</p>";
    }
});
            
        } else {
            console.error("Failed to get coordinates:", data.message);
        }
    })
    .catch(err => {
        console.error("Fetch error:", err);
    });
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


function initHeatMap() {
    if (!heatmap) {
        heatmap = L.map('Heatmap',{
            /*
            zoomControl: false,
            dragging: false,
            scrollWheelZoom: false,
            doubleClickZoom: false,
            boxZoom: false,
            keyboard: false,
            tap: false,
            touchZoom: false*/
        }).setView([0, 0], 13);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 22,
        attribution: '&copy; OpenStreetMap contributors'
        }).addTo(heatmap);
    }
}


function getColorForScore(score) {
    // score should already be between 0 and 1
    if (score < 0.2) return 'blue';
    if (score < 0.4) return 'lime';
    if (score < 0.6) return 'yellow';
    if (score < 0.8) return 'orange';
    return 'red';
}



