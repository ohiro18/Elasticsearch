// Karma configuration
// http://karma-runner.github.io/0.12/config/configuration-file.html
// Generated on 2014-07-17 using
// generator-karma 0.8.3

module.exports = function(config) {
  'use strict';

  config.set({
    autoWatch: false,

    basePath: './',

    frameworks: ['jasmine'],

    files: [
      'bower_components/angular/angular.js',
      'bower_components/elasticsearch/elasticsearch.angular.js',
      'bower_components/angular-mocks/angular-mocks.js',
      'scripts/**/*.js',
      'test/mock/**/*.js',
      'test/spec/**/*.js'
    ],

    // web server port
    port: 8080,

    browsers: [
      'PhantomJS'
    ],

    plugins: [
      'karma-phantomjs-launcher',
      'karma-chrome-launcher',
      'karma-jasmine',
      'karma-coverage'
    ],

    preprocessors: {
      'app/scripts/**/*.js': ['coverage']
    },

    reporters: ['progress', 'coverage'],

    singleRun: true,

    colors: true,

    // level of logging
    // possible values: LOG_DISABLE || LOG_ERROR || LOG_WARN || LOG_INFO || LOG_DEBUG
    logLevel: config.LOG_INFO,
  });
};
