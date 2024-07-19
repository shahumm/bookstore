document.addEventListener("DOMContentLoaded", () => {
  // Search
  const searchBtn = document.getElementById("searchBtn");
  const searchInput = document.getElementById("searchInput");
  const searchSubmitBtn = document.getElementById("searchSubmitBtn");
  const searchResults = document.getElementById("searchResults");
  const searchResultsContainer = document.getElementById(
    "searchResultsContainer"
  );
  const searchTermDisplay = document.getElementById("searchTermDisplay");

  // Category
  const categoriesContainer = document.getElementById("categoriesContainer");

  // Cart
  const cartBtn = document.getElementById("cartBtn");
  const cartDropdown = document.getElementById("cartDropdown");
  const cartItemsContainer = document.getElementById("cartItems");
  const cartCounter = document.getElementById("cartCounter");
  const clearCartBtn = document.getElementById("clearCartBtn");
  const cartTotalElement = document.getElementById("totalPrice");
  let cartItems = [];

  // Modal
  const bookModal = document.getElementById("bookModal");
  const closeModal = document.querySelector(".close");
  const modalBookImage = document.getElementById("modalBookImage");
  const modalBookTitle = document.getElementById("modalBookTitle");
  const modalBookAuthor = document.getElementById("modalBookAuthor");
  const modalBookDescription = document.getElementById("modalBookDescription");
  const modalBookISBN = document.getElementById("modalBookISBN");
  const modalBookPrice = document.getElementById("modalBookPrice");
  const modalBookStock = document.getElementById("modalBookStock");
  const modalAddToCart = document.getElementById("modalAddToCart");

  // --------------------------------- NOTIFICATION ---------------------------------
  const notification = document.getElementById("notification");

  // Show Notification
  function showNotification(message) {
    notification.textContent = message;
    notification.style.display = "block";
    setTimeout(() => {
      notification.style.display = "none";
    }, 1000);
  }

  // ----------------------------------- SEARCHING -----------------------------------

  // Expand NavBar + Focus Search Input
  searchBtn.addEventListener("click", () => {
    const navbar = document.querySelector(".navbar");
    navbar.classList.toggle("expanded");
    if (navbar.classList.contains("expanded")) {
      searchInput.focus();
    }
  });

  // Prevents Page Reload + Performs Search
  searchSubmitBtn.addEventListener("click", (event) => {
    event.preventDefault();
    performSearch();
  });

  // Press Enter to Search
  searchInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      performSearch();
    }
  });

  // Prevents Unintended Actions of Parent Elements When Clicked
  searchInput.addEventListener("click", (event) => {
    event.stopPropagation();
  });

  // Shows Search Submit Button on Focus
  searchInput.addEventListener("focus", () => {
    searchSubmitBtn.style.display = "inline-block";
  });

  // Hides Search Submit Button on Unfocus
  searchInput.addEventListener("blur", () => {
    setTimeout(() => {
      if (!document.activeElement.classList.contains("search-submit-btn")) {
        searchSubmitBtn.style.display = "none";
      }
    }, 100);
  });

  // Collapses NavBar when Clicked Outside
  document.addEventListener("click", (event) => {
    const navbar = document.querySelector(".navbar");
    if (
      !navbar.contains(event.target) &&
      navbar.classList.contains("expanded")
    ) {
      navbar.classList.remove("expanded");
    }
  });

  // Displays Search Results
  function performSearch() {
    const searchTerm = searchInput.value.toLowerCase();
    const productCards = document.querySelectorAll(".product-card");
    let hasResults = false;

    searchResultsContainer.innerHTML = "";

    // Update the search term display
    searchTermDisplay.textContent = searchTerm;

    const matchedProducts = new Set();

    productCards.forEach((card) => {
      const title = card.dataset.title.toLowerCase();
      const author = card.dataset.author.toLowerCase();

      if (title.includes(searchTerm) || author.includes(searchTerm)) {
        if (!matchedProducts.has(card.dataset.id)) {
          matchedProducts.add(card.dataset.id);
          const clonedCard = card.cloneNode(true);
          clonedCard
            .querySelector(".add-to-cart")
            .addEventListener("click", (event) => {
              event.stopPropagation();
              addToCart(clonedCard);
            });
          clonedCard.addEventListener("click", () => {
            showModal(card);
          });
          searchResultsContainer.appendChild(clonedCard);
          hasResults = true;
        }
      }
    });

    if (searchTerm === "") {
      searchResults.style.display = "none";
      categoriesContainer.style.display = "block";
    } else {
      searchResults.style.display = "block";
      categoriesContainer.style.display = "none";

      if (!hasResults) {
        searchResultsContainer.innerHTML = "<p>No results found.</p>";
      }
    }
  }

  // ------------------------------------ CARTING ------------------------------------

  // Adds Event Listeners to Add-to-Cart Buttons and Product Cards
  function attachAddToCartListeners() {
    document.querySelectorAll(".add-to-cart").forEach((button) => {
      button.addEventListener("click", (event) => {
        event.stopPropagation();
        addToCart(button.closest(".product-card"), 1); // Pass 1 as the default quantity
      });
    });

    document.querySelectorAll(".product-card").forEach((card) => {
      card.addEventListener("click", () => {
        showModal(card);
      });
    });
  }

  // Adds a Product to the Cart and Updates the Cart Display
  function addToCart(productCard, quantity = 1) {
    const bookId = productCard.dataset.id;
    const formData = new FormData();
    formData.append("book_id", bookId);
    formData.append("quantity", quantity);

    fetch("/add_to_cart", {
      method: "POST",
      body: formData,
    })
      .then((response) => {
        return response.json();
      })
      .then((data) => {
        if (data.success) {
          showNotification("Item added to cart!");
          const existingItem = cartItems.find((item) => item.id === bookId);
          if (existingItem) {
            existingItem.quantity += quantity;
          } else {
            cartItems.push({
              id: bookId,
              title: productCard.dataset.title,
              author: productCard.dataset.author,
              price: productCard.dataset.price,
              image_path: productCard.querySelector("img").src,
              quantity: data.quantity,
            });
          }
          updateCartDisplay();
        } else {
          showNotification(data.message);
        }
      });
  }

  // Clears Cart for Logged In User
  function clearCart() {
    fetch("/clear_cart", {
      method: "POST",
    })
      .then((response) => {
        if (response.status === 401) {
          window.location.href = "/login";
          return;
        }
        return response.json();
      })
      .then((data) => {
        if (data.success) {
          cartItems = [];
          updateCartDisplay();
        }
      });
  }

  // Updates the Cart Display (Shows Current Cart Items) and Counter
  function updateCartDisplay() {
    cartItemsContainer.innerHTML = "";
    if (cartItems.length === 0) {
      cartItemsContainer.innerHTML = "<p>No items in your cart.</p>";
      cartCounter.textContent = "0";
      cartCounter.style.display = "none";
      cartTotalElement.textContent = "0";
    } else {
      let totalPrice = 0;
      cartItems.forEach((item) => {
        const cartItem = document.createElement("div");
        cartItem.className = "cart-item";
        cartItem.innerHTML = `
                <img src="${item.image_path}" alt="Book Image" class="cart-book-image"/>
                <h3>${item.title}</h3>
                <h4>${item.author}</h4>
                <p class="item-price">Rs. ${item.price}</p>
                <div class="quantity-control">
                    <button class="increment-quantity" data-id="${item.id}">+</button>
                    <span>x ${item.quantity}</span>
                </div>
            `;
        cartItemsContainer.appendChild(cartItem);
        totalPrice += parseFloat(item.price) * item.quantity;
      });
      cartCounter.textContent = cartItems.length;
      cartCounter.style.display = "block";
      document.querySelector(".icon.cart").classList.add("has-items");
      cartTotalElement.textContent = totalPrice.toFixed(2);

      document.querySelectorAll(".increment-quantity").forEach((button) => {
        button.addEventListener("click", () => {
          const bookId = button.dataset.id;
          const productCard = document.querySelector(
            `.product-card[data-id="${bookId}"]`
          );
          addToCart(productCard, 1);
        });
      });
    }
  }

  // GSAP Animation for Modal
  function showModal(card) {
    modalBookImage.src = card.querySelector("img").src;
    modalBookTitle.textContent = card.dataset.title;
    modalBookAuthor.textContent = card.dataset.author;
    modalBookDescription.textContent = card.dataset.description;
    modalBookISBN.textContent = card.dataset.isbn;
    modalBookPrice.textContent = "Rs. " + card.dataset.price;
    modalBookStock.textContent = card.dataset.stock;

    const stock = card.dataset.stock;
    if (stock == 0) {
      modalAddToCart.classList.add("out-of-stock");
      modalAddToCart.textContent = "Out of Stock";
      modalAddToCart.disabled = true;
    } else {
      modalAddToCart.classList.remove("out-of-stock");
      modalAddToCart.textContent = "Add to Cart";
      modalAddToCart.disabled = false;
      modalAddToCart.onclick = () => addToCart(card);
    }

    gsap.fromTo(
      bookModal,
      { opacity: 0, y: 2000 },
      { opacity: 1, y: 0, duration: 0.25, ease: "power2.out" }
    );
    bookModal.style.display = "block";
  }

  closeModal.addEventListener("click", () => {
    gsap.to(bookModal, {
      opacity: 0,
      y: 2000,
      duration: 0.25,
      ease: "power2.in",
      onComplete: () => {
        bookModal.style.display = "none";
      },
    });
  });

  // Click Outside to Close Modal
  window.addEventListener("click", (event) => {
    if (event.target == bookModal) {
      gsap.to(bookModal, {
        opacity: 0,
        y: 2000,
        duration: 0.25,
        ease: "power2.in",
        onComplete: () => {
          bookModal.style.display = "none";
        },
      });
    }
  });

  // Click Outside to Close Cart Dropdown
  document.addEventListener("click", (event) => {
    if (
      !cartBtn.contains(event.target) &&
      !cartDropdown.contains(event.target)
    ) {
      cartDropdown.classList.remove("open");
    }
  });

  // Displays Cart Dropdown
  cartBtn.addEventListener("click", (event) => {
    event.stopPropagation();
    if (ordersDropdown.classList.contains("open")) {
      ordersDropdown.classList.remove("open");
    }
    cartDropdown.classList.toggle("open");
  });

  // Listens for Clear Cart Event
  clearCartBtn.addEventListener("click", clearCart);

  // Load Cart Items When Logged In
  fetch("/get_cart_items")
    .then((response) => {
      if (response.status === 401) {
        return [];
      }
      return response.json();
    })
    .then((data) => {
      if (data.success) {
        cartItems = data.cart_items.map((item) => ({
          id: item.BookID,
          title: item.Title,
          author: item.AuthorName,
          price: item.Price,
          image_path: item.image_path,
          quantity: item.Quantity,
        }));
        updateCartDisplay();
      }
    });

  // Listeners to Existing Product Cards
  attachAddToCartListeners();

  const checkoutCartBtn = document.getElementById("checkoutCartBtn");

  checkoutCartBtn.addEventListener("click", () => {
    fetch("/checkout", {
      method: "POST",
    })
      .then((response) => {
        if (response.status === 401) {
          window.location.href = "/login";
          return;
        }
        return response.json();
      })
      .then((data) => {
        if (data.success) {
          showReceipt(data);
          cartDropdown.classList.remove("open");
          clearCart();
        } else {
          alert(data.message);
        }
      });
  });

  // Generate Receipt
  function showReceipt(data) {
    const receiptModal = document.getElementById("receiptModal");
    const receiptContent = document.getElementById("receiptContent");
    const tickAnimation = document.getElementById("tickAnimation");

    const itemCount = data.items.reduce(
      (total, item) => total + item.Quantity,
      0
    );
    const headerText =
      itemCount === 1
        ? "Your new book is on its way!"
        : "Your new books are on their way!";

    receiptContent.innerHTML = `
      <h2>${headerText}</h2>
      <h3>Order Details</h3>
      <p>Order ID: ${data.order_id}</p>
      <p>Order Date: ${data.order_date}</p>

      <ul>
        ${data.items
          .map(
            (item) => `
          <li>
            ${item.Title} by ${item.AuthorName} - Rs. ${item.Price} x ${item.Quantity}
          </li>
        `
          )
          .join("")}
      </ul>

      <h3>Shipping Address</h3>
      <p>${data.user.FirstName}</p>
      <p>${data.user.Address}</p>
      <p>${data.user.City}, ${data.user.Country}</p>
      <p>Email: ${data.user.Email}</p>

      <h3>Payment Details</h3>
      <p>Payment Method: ${data.payment_method}</p>
      <h1>Total: Rs. ${data.total.toFixed(2)}</h1>

    `;
    tickAnimation.style.display = "block";
    receiptModal.style.display = "block";

    // Displays Confetti Animation
    confetti({
      particleCount: 100,
      spread: 70,
      origin: { y: 0.6 },
    });
  }

  const closeReceiptModal = document.querySelector(".close-receipt");
  closeReceiptModal.addEventListener("click", () => {
    document.getElementById("receiptModal").style.display = "none";
    document.getElementById("tickAnimation").style.display = "none";
  });

  window.addEventListener("click", (event) => {
    const receiptModal = document.getElementById("receiptModal");
    if (event.target == receiptModal) {
      receiptModal.style.display = "none";
      document.getElementById("tickAnimation").style.display = "none";
    }
  });
});

// ------------------------------------- ORDERS --------------------------------------

document.addEventListener("DOMContentLoaded", () => {
  const ordersBtn = document.getElementById("ordersBtn");
  const ordersDropdown = document.getElementById("ordersDropdown");
  const ordersItemsContainer = document.getElementById("ordersItems");

  function fetchOrders() {
    fetch("/get_orders")
      .then((response) => {
        if (response.status === 401) {
          return [];
        }
        return response.json();
      })
      .then((data) => {
        if (data.success) {
          updateOrdersDisplay(data.orders);
        }
      })
      .catch((error) => {
        console.error("Error fetching orders:", error);
      });
  }

  // Update Orders Dropdown
  function updateOrdersDisplay(orders) {
    ordersItemsContainer.innerHTML = "";
    if (orders.length === 0) {
      ordersItemsContainer.innerHTML = "<p>No orders found.</p>";
    } else {
      orders.forEach((order) => {
        const ordersItem = document.createElement("div");
        ordersItem.className = "orders-item";
        ordersItem.innerHTML = `
          <div>
            <h3>Order ID: ${order.OrderID}</h3>
            <h4>Order Date: ${order.OrderDate}</h4>
            <ul>
              ${order.items
                .map(
                  (item) => `
                <li>${item.Quantity} x ${item.Title} by ${item.AuthorName} - Rs. ${item.Price}</li>
              `
                )
                .join("")}
            </ul>
            <p>Total: Rs. ${order.Total}</p>
          </div>
        `;
        ordersItemsContainer.appendChild(ordersItem);
      });
    }
  }

  // Open/Close Orders Dropdown
  ordersBtn.addEventListener("click", (event) => {
    event.stopPropagation();
    if (cartDropdown.classList.contains("open")) {
      cartDropdown.classList.remove("open");
    }
    ordersDropdown.classList.toggle("open");
  });

  // Click Outside to Close Order Dropdown
  document.addEventListener("click", (event) => {
    if (
      !ordersBtn.contains(event.target) &&
      !ordersDropdown.contains(event.target)
    ) {
      ordersDropdown.classList.remove("open");
    }
  });

  // Initial Orders Load
  fetchOrders();

  const productCards = document.querySelectorAll(".product-card");

  productCards.forEach((card) => {
    const stock = card.dataset.stock;
    const addToCartButton = card.querySelector(".add-to-cart");

    if (stock == 0) {
      card.classList.add("out-of-stock");
      addToCartButton.disabled = true;
    }
  });
});
