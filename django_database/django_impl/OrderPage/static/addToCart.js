console.log("addToCart.js loaded!");
let currentFoodItem = null; // To store the currently selected food item
const viewCartBtn = document.getElementById('viewCartBtn');
const cartItemCountSpan = document.getElementById('cartItemCount');
let cartItemCount = 0; // Initialize cart count
let cartItems = []; // Array to store food items, quantity, and price

function updateCartButton() {
    if (cartItemCount > 0) {
        viewCartBtn.style.display = 'inline-block'; // Show the button
        cartItemCountSpan.textContent = cartItemCount; // Update the count
    } else {
        viewCartBtn.style.display = 'none'; // Hide the button if cart is empty
        cartItemCountSpan.textContent = 0;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const storedCart = localStorage.getItem('cart');
    if (storedCart) {
        cartItems = JSON.parse(storedCart);
        cartItemCount = cartItems.reduce((sum, item) => sum + item.quantity, 0);
        updateCartButton();
    }
});



viewCartBtn.addEventListener('click', () => {
    // Store the cartItems in local storage before navigating
    // localStorage.setItem('cart', JSON.stringify(cartItems));
    // In addToOrder() or when going to /cart/
    fetch('/your_django_cart_view/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
        },
        body: JSON.stringify(cartItems), // Sending the cartItems array
    })
    .then(response => response.json())
    .then(data => {
        // Handle the response from your Django view
        console.log(data);
        window.location.href = '/cart/';
    })
    .catch(error => {
        console.error('Error sending cart data:', error);
    });

});

function showQuantityPopup(foodItem) {
    currentFoodItem = foodItem;
    document.getElementById('foodName').textContent = foodItem.name;
    document.getElementById('quantity').value = 1; // Reset quantity
    document.getElementById('quantityPopup').style.display = 'block';
}

function closePopup() {
    document.getElementById('quantityPopup').style.display = 'none';
    currentFoodItem = null;
}

function increaseQuantity() {
    let quantityInput = document.getElementById('quantity');
    quantityInput.value = parseInt(quantityInput.value) + 1;
}

function decreaseQuantity() {
    let quantityInput = document.getElementById('quantity');
    let currentValue = parseInt(quantityInput.value);
    if (currentValue > 1) {
        quantityInput.value = currentValue - 1;
    }
}

function addToOrder() {
    if (currentFoodItem) {
        const quantity = parseInt(document.getElementById('quantity').value);

        // Check if the item is already in the cart
        const existingItemIndex = cartItems.findIndex(item => item.name === currentFoodItem.name);

        if (existingItemIndex > -1) {
            // If it exists, update the quantity
            cartItems[existingItemIndex].quantity += quantity;
        } else {
            // If it's a new item, add it to the cart
            cartItems.push({
                name: currentFoodItem.name,
                quantity: quantity,
                price: currentFoodItem.price
            });
        }

        // Update the cart item count
        cartItemCount = cartItems.reduce((sum, item) => sum + item.quantity, 0);
        updateCartButton();

        // Optionally, store the updated cart in local storage immediately
        localStorage.setItem('cart', JSON.stringify(cartItems));

        closePopup();
    }
}

const foodTabs = document.querySelectorAll('.FoodTab.Items');
foodTabs.forEach(tab => {
    tab.addEventListener('click', function() {
        const foodName = this.querySelector('p:nth-child(2)').textContent;
        const foodPrice = this.querySelector('p:nth-child(3)').textContent;
        const foodPic = this.querySelector('img').src;

        const foodItem = {
            name: foodName,
            price: foodPrice,
            pic: foodPic
        };
        showQuantityPopup(foodItem);
    });
});

document.getElementById('checkoutBtn').addEventListener('click', function() {
    window.location.href = '/index/';
});

//End of Cart Functions End of Cart Functions
//End of Cart Functions End of Cart Functions
//End of Cart Functions End of Cart Functions