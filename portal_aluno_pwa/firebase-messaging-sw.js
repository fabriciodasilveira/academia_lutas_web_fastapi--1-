importScripts('https://www.gstatic.com/firebasejs/10.8.0/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/10.8.0/firebase-messaging-compat.js');

firebase.initializeApp({
    apiKey: "AIzaSyDpmpgccC-DP9LqqPHORw34OowPa0IGn5Q",
    projectId: "fightclube-f8913",
    messagingSenderId: "826801342288",
    appId: "1:826801342288:web:0d56174de8d9e1d2510e55"
});

const messaging = firebase.messaging();

messaging.onBackgroundMessage((payload) => {
    const notificationTitle = payload.notification.title;
    const notificationOptions = {
        body: payload.notification.body,
        icon: '/portal/images/icone.png',
        data: { url: payload.data.url }
    };
    self.registration.showNotification(notificationTitle, notificationOptions);
});