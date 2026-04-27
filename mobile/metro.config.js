/**
 * Metro config para ReadyDay.
 * watchFolders incluye el directorio padre para que Metro pueda
 * resolver imports de ../shared-types/ desde los archivos domain/ y garmin/.
 */
const { getDefaultConfig } = require('expo/metro-config');
const path = require('path');

const config = getDefaultConfig(__dirname);

// Permitir imports fuera del directorio mobile/ (shared-types/, etc.)
config.watchFolders = [path.resolve(__dirname, '..')];

module.exports = config;
