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
            close.addEventListener("click", function(){
                mo.style.display = "none"
            })
            ShowItemModal.forEach(Mod => {
                Mod.addEventListener("click", function(){
                    const items = el.dataset.items; 
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
    
})
