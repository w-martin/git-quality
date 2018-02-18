'use strict';

/**
 * git-quality scripts
 *
 * Functionality:
 * - Initialise mobile menu functionality
 * - - Toggle the mobile menu UI elements
 * - - Toggle the mobile menu state config
 */
(function() {
    // Find all mobile menu buttons
    var mobileMenuToggles = document.querySelectorAll('.toggle-mobile-menu');
    var openMenuButton = document.querySelector('.open-menu');
    var closeMenuButton = document.querySelector('.close-menu');

    // Find DOM nodes needed for mobile menu transitions
    var navigation = document.querySelector('nav');
    var header = document.querySelector('header');

    // Store state info to help with the mobile menu
    var state = {
        mobileMenuOpen: false,
        updatingMenu: false,
        animationOffset: 400
    };

    /**
     * Toggle the mobile related config stored in the state
    */
    function toggleMobileState() {
        state.mobileMenuOpen = !state.mobileMenuOpen;
        state.updatingMenu = !state.updatingMenu;
    }

    /**
     * Toggle the mobile menu visibility based on [state.mobileMenuOpen]
    */
    function toggleMobileMenu() {
        // Best to wait for this to finish
        if (!state.updatingMenu) {
            state.updatingMenu = true;

            if (state.mobileMenuOpen) {
                // Reset the top position of the navigation
                navigation.style.top = '';

                // Fade out the close menu button
                closeMenuButton.style.opacity = '';

                // Wait for the previous animations to finish
                setTimeout(function() {
                    // Fade in the open menu button
                    openMenuButton.style.opacity = '';

                    // Toggle the config
                    toggleMobileState();
                }, state.animationOffset);
            } else {
                // Slide down the navigation
                navigation.style.top = '9vh';

                // Fade out the open menu button
                openMenuButton.style.opacity = 0;

                // Wait for the previous animations to finish
                setTimeout(function() {
                    // Fade in the close menu button
                    closeMenuButton.style.opacity = 1;

                    // Toggle the config
                    toggleMobileState();
                }, state.animationOffset);
            }
        }
    }

    /**
     * Check to see if the mobile menu can be initialised
    */
    function initialiseMobileMenu() {
        // Can we find what we need to intialise...
        if (mobileMenuToggles.length && openMenuButton && closeMenuButton) {
            // All needed nodes found, add click events to the open and close buttons
            Array.from(mobileMenuToggles).forEach(function(toggleButton) {
                toggleButton.addEventListener('click', toggleMobileMenu);
            });

            // Watch for the screen width changing and hide the mobile menu on larger screens
            window.onresize = function() {
                if (window.innerWidth > 768 && state.mobileMenuOpen) {
                    toggleMobileMenu();
                }
            };
        } else {
            // Uh-oh...
            console.warn('I can\'t find the mobile menu buttons');
        }
    }

    // Let's go!
    initialiseMobileMenu();
}());
