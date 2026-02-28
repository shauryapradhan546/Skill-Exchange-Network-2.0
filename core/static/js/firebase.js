// ============================================
// FIREBASE CONFIGURATION & INITIALIZATION
// ============================================
//
// This file handles all Firebase integration:
//   1. Firebase SDK initialization with project credentials
//   2. Authentication (email/password, Google sign-in)
//   3. Auth state management (detect login/logout)
//   4. Firestore database operations (save/read documents)
//   5. Firebase Storage (file uploads)
//   6. API fetch helper that includes Firebase token + CSRF token
//
// How Firebase auth works with Django:
//   - User authenticates with Firebase (client-side, in the browser)
//   - Firebase gives us an ID token (JWT)
//   - We send that token to our Django backend (/firebase-login/)
//   - Django verifies the token and creates a session
//   - Now the user is authenticated in both Firebase AND Django
//
// Dependencies: Firebase SDK (loaded via CDN in base.html)
// ============================================

// Firebase project credentials — loaded from environment variables via Django
// The config is injected into window.FIREBASE_CONFIG by base.html
// (which reads it from settings.py → .env file)
const firebaseConfig = window.FIREBASE_CONFIG || {};

if (!window.FIREBASE_CONFIG) {
    console.warn('⚠️ Firebase config not found on window.FIREBASE_CONFIG. Make sure base.html is loaded first.');
}

// Firebase service instances — initialized once, used throughout the file
let app, auth, db, storage;
let firebaseInitialized = false;

/**
 * Initialize Firebase SDK with our project config.
 * Called once on page load. Checks if the SDK is even loaded first
 * (it might not be if the CDN fails to load).
 */
function initializeFirebase() {
    try {
        // Check if Firebase SDK was loaded from the CDN
        if (typeof firebase === 'undefined') {
            console.warn('⚠️ Firebase SDK not loaded');
            return false;
        }

        // Only initialize once — firebase.apps.length tracks initialized apps
        if (!firebase.apps.length) {
            app = firebase.initializeApp(firebaseConfig);
            auth = firebase.auth();
            db = firebase.firestore();
            storage = firebase.storage();
            firebaseInitialized = true;
            console.log('✅ Firebase initialized successfully');

            // Start listening for auth state changes (login/logout events)
            setupAuthStateListener();
        }
        return true;
    } catch (error) {
        console.error('❌ Firebase initialization error:', error);
        return false;
    }
}

// Auto-initialize when this script loads
initializeFirebase();


// ============================================
// DJANGO CSRF TOKEN HELPER
// ============================================
// Django requires a CSRF token for POST requests to prevent
// cross-site request forgery. We read it from the browser cookies.

/**
 * Read a cookie value by name from document.cookie.
 * Django stores the CSRF token in a cookie called 'csrftoken'.
 */
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Read the CSRF token once and reuse it for all requests
const csrftoken = getCookie('csrftoken');


// ============================================
// AUTHENTICATION FUNCTIONS
// ============================================

/**
 * Get the current user's Firebase ID token (JWT).
 * This token is sent to the Django backend for verification.
 * Returns null if no user is signed in.
 */
async function getIdToken() {
    if (!firebaseInitialized) return null;

    try {
        const user = auth.currentUser;
        if (user) {
            return await user.getIdToken(); // Firebase refreshes expired tokens automatically
        }
        return null;
    } catch (error) {
        console.error('Error getting ID token:', error);
        return null;
    }
}

/**
 * Sign in with email and password via Firebase.
 * After Firebase authenticates, sends the token to Django for server-side session creation.
 */
async function firebaseLogin(email, password) {
    if (!firebaseInitialized) {
        return { success: false, error: 'Firebase not initialized' };
    }

    try {
        // Step 1: Authenticate with Firebase
        const userCredential = await auth.signInWithEmailAndPassword(email, password);
        const user = userCredential.user;
        const idToken = await user.getIdToken();

        // Step 2: Send token to Django backend for verification
        const response = await apiFetch('/api/auth/verify-token/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ token: idToken })
        });

        const data = await response.json();

        if (data.success) {
            console.log('✅ Firebase login successful');
            return { success: true, user: user, data: data };
        } else {
            return { success: false, error: data.error || 'Login failed' };
        }
    } catch (error) {
        console.error('❌ Firebase login error:', error);
        return { success: false, error: error.message };
    }
}

/**
 * Register a new user with email and password via Firebase.
 * Also sets the display name and sends credentials to Django.
 */
async function firebaseRegister(email, password, userData) {
    if (!firebaseInitialized) {
        return { success: false, error: 'Firebase not initialized' };
    }

    try {
        // Step 1: Create Firebase user
        const userCredential = await auth.createUserWithEmailAndPassword(email, password);
        const user = userCredential.user;

        // Step 2: Set display name in Firebase profile
        await user.updateProfile({
            displayName: `${userData.firstName} ${userData.lastName}`
        });

        // Step 3: Get token and send to Django
        const idToken = await user.getIdToken();

        const response = await apiFetch('/api/auth/verify-token/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                token: idToken,
                userData: userData
            })
        });

        const data = await response.json();

        console.log('✅ Firebase registration successful');
        return { success: true, user: user, data: data };
    } catch (error) {
        console.error('❌ Firebase registration error:', error);
        return { success: false, error: error.message };
    }
}

/**
 * Sign out from Firebase. Django session is handled separately
 * (the user should also hit the /logout/ URL to clear Django's session).
 */
async function firebaseLogout() {
    if (!firebaseInitialized) return { success: false };

    try {
        await auth.signOut();
        console.log('✅ Firebase logout successful');
        return { success: true };
    } catch (error) {
        console.error('❌ Logout error:', error);
        return { success: false, error: error.message };
    }
}

/**
 * Sign in with Google popup.
 * Firebase handles the entire OAuth flow (popup, token exchange, etc.)
 */
async function signInWithGoogle() {
    if (!firebaseInitialized) {
        return { success: false, error: 'Firebase not initialized' };
    }

    try {
        // GoogleAuthProvider triggers the "Sign in with Google" popup
        const provider = new firebase.auth.GoogleAuthProvider();
        const result = await auth.signInWithPopup(provider);
        const user = result.user;
        const idToken = await user.getIdToken();

        // Send to Django for server-side session
        const response = await apiFetch('/api/auth/verify-token/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ token: idToken })
        });

        const data = await response.json();
        console.log('✅ Google sign-in successful');
        return { success: true, user: user, data: data };
    } catch (error) {
        console.error('❌ Google sign-in error:', error);
        return { success: false, error: error.message };
    }
}

/**
 * Listen for auth state changes (user logs in or out).
 * Firebase calls this callback whenever the auth state changes,
 * including on page load (to restore the previous session).
 */
function setupAuthStateListener() {
    if (!firebaseInitialized) return;

    auth.onAuthStateChanged(async (user) => {
        if (user) {
            console.log('✅ User is signed in:', user.email);

            // Update UI to show logged-in state
            updateAuthUI(true, user);

            // Cache the token in localStorage for quick access
            const token = await getIdToken();
            if (token) {
                localStorage.setItem('firebaseToken', token);
            }
        } else {
            console.log('ℹ️ User is signed out');
            updateAuthUI(false, null);
            localStorage.removeItem('firebaseToken');
        }
    });
}

/**
 * Update the page UI based on authentication state.
 * Shows/hides elements with .login-required and .logout-required classes.
 */
function updateAuthUI(isAuthenticated, user) {
    const loginLinks = document.querySelectorAll('.login-required');
    const logoutLinks = document.querySelectorAll('.logout-required');

    if (isAuthenticated) {
        loginLinks.forEach(el => el.style.display = 'block');
        logoutLinks.forEach(el => el.style.display = 'none');

        // Update all elements showing the user's name
        const userNameElements = document.querySelectorAll('.user-name');
        userNameElements.forEach(el => {
            el.textContent = user.displayName || user.email;
        });
    } else {
        loginLinks.forEach(el => el.style.display = 'none');
        logoutLinks.forEach(el => el.style.display = 'block');
    }
}


// ============================================
// API FETCH HELPER (WITH FIREBASE & CSRF)
// ============================================

/**
 * Enhanced fetch() wrapper that automatically adds:
 *   - Firebase ID token in the Authorization header (for API auth)
 *   - Django CSRF token in X-CSRFToken header (for form protection)
 *   - Default Content-Type of application/json
 *
 * Use this instead of plain fetch() for all API calls.
 *
 * Example:
 *   const response = await apiFetch('/api/notifications/', { method: 'GET' });
 *   const data = await response.json();
 */
async function apiFetch(url, options = {}) {
    const token = await getIdToken();
    const headers = options.headers || {};

    // Add Firebase auth token if user is signed in
    if (token) {
        headers['Authorization'] = 'Bearer ' + token;
    }

    // Add CSRF token for state-changing requests
    if (['POST', 'PUT', 'DELETE', 'PATCH'].includes(options.method?.toUpperCase())) {
        headers['X-CSRFToken'] = csrftoken;
    }

    // Default to JSON content type if sending a body
    if (!headers['Content-Type'] && options.body) {
        headers['Content-Type'] = 'application/json';
    }

    return fetch(url, { ...options, headers });
}


// ============================================
// FIRESTORE OPERATIONS
// ============================================
// These functions interact with Firebase's Firestore database.
// Currently used for supplementary data storage
// (main data is in Django's SQLite database).

/**
 * Save a document to a Firestore collection.
 * Automatically adds a createdAt timestamp.
 */
async function saveToFirestore(collection, data) {
    if (!firebaseInitialized) return { success: false };

    try {
        const docRef = await db.collection(collection).add({
            ...data,
            createdAt: firebase.firestore.FieldValue.serverTimestamp()
        });

        console.log('✅ Document written with ID:', docRef.id);
        return { success: true, id: docRef.id };
    } catch (error) {
        console.error('❌ Firestore save error:', error);
        return { success: false, error: error.message };
    }
}

/**
 * Read a single document from Firestore by its ID.
 */
async function getFromFirestore(collection, docId) {
    if (!firebaseInitialized) return { success: false };

    try {
        const docRef = db.collection(collection).doc(docId);
        const doc = await docRef.get();

        if (doc.exists) {
            return { success: true, data: doc.data() };
        } else {
            return { success: false, error: 'Document not found' };
        }
    } catch (error) {
        console.error('❌ Firestore get error:', error);
        return { success: false, error: error.message };
    }
}


// ============================================
// STORAGE OPERATIONS
// ============================================

/**
 * Upload a file to Firebase Storage and get its download URL.
 *
 * @param {File} file - The file object to upload
 * @param {string} path - Storage path (e.g., 'avatars/user123.jpg')
 * @returns {Object} { success, url } or { success: false, error }
 */
async function uploadFile(file, path) {
    if (!firebaseInitialized) return { success: false };

    try {
        const storageRef = storage.ref();
        const fileRef = storageRef.child(path);

        const snapshot = await fileRef.put(file);
        const downloadURL = await snapshot.ref.getDownloadURL();

        console.log('✅ File uploaded successfully');
        return { success: true, url: downloadURL };
    } catch (error) {
        console.error('❌ Upload error:', error);
        return { success: false, error: error.message };
    }
}


// ============================================
// UTILITY FUNCTIONS
// ============================================

/** Get the currently signed-in Firebase user object, or null. */
function getCurrentUser() {
    return firebaseInitialized ? auth.currentUser : null;
}

/** Check if Firebase has been initialized successfully. */
function isFirebaseReady() {
    return firebaseInitialized;
}


// ============================================
// EXPORT — Make functions available globally
// ============================================
// Attach to window object so other scripts and inline
// event handlers can call these functions.

window.firebaseAuth = {
    login: firebaseLogin,
    register: firebaseRegister,
    logout: firebaseLogout,
    googleSignIn: signInWithGoogle,
    getCurrentUser: getCurrentUser,
    getIdToken: getIdToken,
    isReady: isFirebaseReady
};

window.apiFetch = apiFetch;

console.log('🔥 Firebase module loaded');
