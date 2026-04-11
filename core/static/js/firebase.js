import { initializeApp } from 'https://www.gstatic.com/firebasejs/10.7.1/firebase-app.js';
import {
    getAuth,
    signInWithPopup,
    getRedirectResult,
    GoogleAuthProvider,
    signInWithEmailAndPassword,
    createUserWithEmailAndPassword
} from 'https://www.gstatic.com/firebasejs/10.7.1/firebase-auth.js';

const app = initializeApp(window.FIREBASE_CONFIG);
const auth = getAuth(app);
const googleProvider = new GoogleAuthProvider();

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

window.firebaseAuth = {
    googleSignIn: async () => {
        const result = await signInWithPopup(auth, googleProvider);
        await sendToDjango(result.user);
        window.location.href = '/profile/';
    },
    emailSignIn: async (email, password) => {
        try {
            const result = await signInWithEmailAndPassword(auth, email, password);
            return { success: true, user: result.user };
        } catch (error) {
            return { success: false, error: error.message, code: error.code };
        }
    },
    emailSignUp: async (email, password) => {
        try {
            const result = await createUserWithEmailAndPassword(auth, email, password);
            return { success: true, user: result.user };
        } catch (error) {
            return { success: false, error: error.message, code: error.code };
        }
    }
};
