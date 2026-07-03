import { initializeApp } from 'https://www.gstatic.com/firebasejs/10.7.1/firebase-app.js';
import {
    getAuth,
    signInWithPopup,
    getRedirectResult,
    GoogleAuthProvider,
    signInWithEmailAndPassword,
    createUserWithEmailAndPassword
} from 'https://www.gstatic.com/firebasejs/10.7.1/firebase-auth.js';

let app = null;
let auth = null;
let googleProvider = null;

const isFirebaseConfigured = window.FIREBASE_CONFIG && 
    window.FIREBASE_CONFIG.apiKey && 
    window.FIREBASE_CONFIG.apiKey !== 'your-firebase-api-key' && 
    window.FIREBASE_CONFIG.apiKey !== '';

if (isFirebaseConfigured) {
    app = initializeApp(window.FIREBASE_CONFIG);
    auth = getAuth(app);
    googleProvider = new GoogleAuthProvider();

    getRedirectResult(auth).then(async result => {
        if (result && result.user) {
            try {
                await sendToDjango(result.user);
                window.location.href = '/profile/';
            } catch (e) {
                console.error('Firebase redirect auth failed:', e);
            }
        }
    }).catch(() => {});
} else {
    console.warn('Firebase is not configured or uses placeholder credentials. Google/Firebase authentication features will be disabled.');
}

async function sendToDjango(user) {
    const resp = await fetch('/firebase-login/', {
        method: 'POST',
        credentials: 'same-origin',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            uid: user.uid,
            email: user.email,
            displayName: user.displayName,
            photoURL: user.photoURL
        })
    });
    if (!resp.ok) throw new Error('Server responded with status ' + resp.status);
    const data = await resp.json();
    if (!data.success) throw new Error(data.error || 'Authentication failed on server');
}

window.firebaseAuth = {
    googleSignIn: async () => {
        if (!isFirebaseConfigured) {
            alert('Google authentication is not configured for this server environment.');
            return;
        }
        const result = await signInWithPopup(auth, googleProvider);
        await sendToDjango(result.user);
        window.location.href = '/profile/';
    },
    emailSignIn: async (email, password) => {
        if (!isFirebaseConfigured) {
            return { success: false, error: 'Firebase authentication is not configured.' };
        }
        try {
            const result = await signInWithEmailAndPassword(auth, email, password);
            return { success: true, user: result.user };
        } catch (error) {
            return { success: false, error: error.message, code: error.code };
        }
    },
    emailSignUp: async (email, password) => {
        if (!isFirebaseConfigured) {
            return { success: false, error: 'Firebase authentication is not configured.' };
        }
        try {
            const result = await createUserWithEmailAndPassword(auth, email, password);
            return { success: true, user: result.user };
        } catch (error) {
            return { success: false, error: error.message, code: error.code };
        }
    }
};
