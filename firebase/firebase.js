// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getAnalytics } from "firebase/analytics";
// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
const firebaseConfig = {
  apiKey: "AIzaSyBa-wGdWpE7hjDiuH4nvI60HXmyyGYVZYQ",
  authDomain: "gitoracle-bfe28.firebaseapp.com",
  projectId: "gitoracle-bfe28",
  storageBucket: "gitoracle-bfe28.firebasestorage.app",
  messagingSenderId: "720373131209",
  appId: "1:720373131209:web:ec14166d07f618589c2a18",
  measurementId: "G-Z0C2VQ2DH3"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const analytics = getAnalytics(app);