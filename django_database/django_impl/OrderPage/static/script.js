console.log("script.js loaded!");
document.addEventListener("DOMContentLoaded", function(){
        
        let tabs = document.querySelectorAll(".restaurant_tab")
        if(tabs){
            tabs.forEach(tab => {
                tab.addEventListener("click", function(){
                    const id = tab.dataset.id;
                    window.location.href = "/pages/" + parseInt(id) +"/"
                })
            })
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
        if(ShowItemModal){
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
        if(ShowModal){
            let mo = document.querySelector("#DeliModal")
            let co = document.querySelector("#DelimodalContent")
            let close = document.querySelector(".close")
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
        if(completeOrder){
            completeOrder.forEach(btn => {
               
                btn.addEventListener("click", function(){
                    let oid = this.orderId
                    fetch('PrepareOrder/' + oid, {
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
                            button.disabled = true;
                            button.textContent = 'Order finished';
                        } else {
                            alert('Failed to complete order');
                        }
                        window.location.href = "/index"
                    });
                })
            })
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
            ordersContainer.innerHTML = '';  // Clear old content

            data.orders.forEach(order => {
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