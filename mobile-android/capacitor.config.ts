import { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'co.readyday.app',
  appName: 'ReadyDay',
  webDir: 'web',

  // Carga la UI desde el servidor (hot-reload automático cuando actualizas el frontend)
  server: {
    url: 'https://www.fergussononline.org/readyday/',
    cleartext: false,
    allowNavigation: ['fergussononline.org'],
  },

  android: {
    backgroundColor: '#07070F',
    allowMixedContent: false,
    captureInput: true,
    // Necesario para Health Connect
    minWebViewVersion: 60,
  },

  plugins: {
    SplashScreen: {
      launchShowDuration: 1500,
      backgroundColor: '#07070F',
      showSpinner: false,
    },
    PushNotifications: {
      presentationOptions: ['badge', 'sound', 'alert'],
    },
    LocalNotifications: {
      smallIcon: 'ic_stat_icon',
      iconColor: '#00D4AA',
      sound: 'default',
    },
  },
};

export default config;
