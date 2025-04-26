// Main JavaScript file for E-commerce Website

// Quantity increment/decrement controls
function setupQuantityControls() {
    const decrementBtns = document.querySelectorAll('.decrement-quantity');
    const incrementBtns = document.querySelectorAll('.increment-quantity');
    
    if (decrementBtns) {
        decrementBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                const input = this.nextElementSibling;
                const currentValue = parseInt(input.value);
                if (currentValue > 1) {
                    input.value = currentValue - 1;
                }
            });
        });
    }
    
    if (incrementBtns) {
        incrementBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                const input = this.previousElementSibling;
                const currentValue = parseInt(input.value);
                const max = parseInt(input.getAttribute('max') || 100);
                if (currentValue < max) {
                    input.value = currentValue + 1;
                }
            });
        });
    }
}

// PIN code validation
function setupPincodeValidation() {
    const pincodeInput = document.getElementById('pincode');
    const pincodeValidationMsg = document.getElementById('pincode-validation-msg');
    
    if (pincodeInput && pincodeValidationMsg) {
        pincodeInput.addEventListener('blur', function() {
            const pincode = this.value.trim();
            
            if (pincode.length === 6 && /^\d+$/.test(pincode)) {
                // Send Ajax request to validate pincode
                const formData = new FormData();
                formData.append('pincode', pincode);
                
                fetch('/pincode/validate', {
                    method: 'POST',
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    if (data.valid) {
                        pincodeValidationMsg.textContent = 'Delivery available at this location';
                        pincodeValidationMsg.className = 'text-success';
                    } else {
                        pincodeValidationMsg.textContent = 'Sorry, delivery not available at this location';
                        pincodeValidationMsg.className = 'text-danger';
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    pincodeValidationMsg.textContent = 'Error validating PIN code';
                    pincodeValidationMsg.className = 'text-danger';
                });
            } else if (pincode !== '') {
                pincodeValidationMsg.textContent = 'Please enter a valid 6-digit PIN code';
                pincodeValidationMsg.className = 'text-danger';
            } else {
                pincodeValidationMsg.textContent = '';
            }
        });
    }
}

// Payment method selection
function setupPaymentMethodSelection() {
    const paymentCards = document.querySelectorAll('.payment-method-card');
    const paymentMethodInput = document.getElementById('payment_method');
    
    if (paymentCards && paymentMethodInput) {
        paymentCards.forEach(card => {
            card.addEventListener('click', function() {
                // Remove 'selected' class from all cards
                paymentCards.forEach(c => c.classList.remove('selected'));
                
                // Add 'selected' class to the clicked card
                this.classList.add('selected');
                
                // Update the hidden input value
                const method = this.getAttribute('data-method');
                paymentMethodInput.value = method;
            });
        });
    }
}

// Address selection
function setupAddressSelection() {
    const addressCards = document.querySelectorAll('.address-card');
    const addressRadios = document.querySelectorAll('input[name="address_id"]');
    
    if (addressCards && addressRadios) {
        addressCards.forEach(card => {
            card.addEventListener('click', function() {
                const addressId = this.getAttribute('data-address-id');
                
                // Find the corresponding radio input and check it
                const radio = document.querySelector(`input[name="address_id"][value="${addressId}"]`);
                if (radio) {
                    radio.checked = true;
                    
                    // Update UI - remove 'selected' class from all cards and add to clicked one
                    addressCards.forEach(c => c.classList.remove('selected'));
                    this.classList.add('selected');
                }
            });
        });
        
        // Also handle when radio is clicked directly
        addressRadios.forEach(radio => {
            radio.addEventListener('change', function() {
                if (this.checked) {
                    const addressId = this.value;
                    
                    // Update UI - remove 'selected' class from all cards and add to corresponding card
                    addressCards.forEach(c => c.classList.remove('selected'));
                    const selectedCard = document.querySelector(`.address-card[data-address-id="${addressId}"]`);
                    if (selectedCard) {
                        selectedCard.classList.add('selected');
                    }
                }
            });
        });
    }
}

// Price range filter
function setupPriceRangeFilter() {
    const priceRangeMin = document.getElementById('price-range-min');
    const priceRangeMax = document.getElementById('price-range-max');
    const priceMinValue = document.getElementById('price-min-value');
    const priceMaxValue = document.getElementById('price-max-value');
    
    if (priceRangeMin && priceRangeMax && priceMinValue && priceMaxValue) {
        priceRangeMin.addEventListener('input', function() {
            const minVal = parseInt(this.value);
            const maxVal = parseInt(priceRangeMax.value);
            
            if (minVal > maxVal) {
                priceRangeMax.value = minVal;
                priceMaxValue.textContent = minVal;
            }
            
            priceMinValue.textContent = minVal;
        });
        
        priceRangeMax.addEventListener('input', function() {
            const maxVal = parseInt(this.value);
            const minVal = parseInt(priceRangeMin.value);
            
            if (maxVal < minVal) {
                priceRangeMin.value = maxVal;
                priceMinValue.textContent = maxVal;
            }
            
            priceMaxValue.textContent = maxVal;
        });
    }
}

// Initialize all functions when DOM is fully loaded
document.addEventListener('DOMContentLoaded', function() {
    setupQuantityControls();
    setupPincodeValidation();
    setupPaymentMethodSelection();
    setupAddressSelection();
    setupPriceRangeFilter();
    
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    if (alerts) {
        alerts.forEach(alert => {
            setTimeout(() => {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }, 5000);
        });
    }
});
