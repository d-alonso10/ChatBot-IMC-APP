plugins {
    id("com.android.application")
    id("kotlin-android")
    // --- ¡AÑADIDO! ---
    id("com.google.gms.google-services")
    // --- FIN ---
    id("dev.flutter.flutter-gradle-plugin")
}

android {
    namespace = "com.example.frontend"
    compileSdk = flutter.compileSdkVersion
    ndkVersion = flutter.ndkVersion

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_11
        targetCompatibility = JavaVersion.VERSION_11
    }

    kotlinOptions {
        jvmTarget = JavaVersion.VERSION_11.toString()
    }

    defaultConfig {
        applicationId = "com.example.frontend"
        minSdk = flutter.minSdkVersion
        targetSdk = flutter.targetSdkVersion
        versionCode = flutter.versionCode
        versionName = flutter.versionName
        
        // --- ¡AÑADIDO! ---
        // Habilitar multidex, requerido por Firebase
        multiDexEnabled = true
        // --- FIN ---
    }

    buildTypes {
        release {
            signingConfig = signingConfigs.getByName("debug")
        }
    }
}

flutter {
    source = "../.."
}

dependencies {
    // --- ¡AÑADIDO! ---
    // Importar la lista de materiales (Bill of Materials) de Firebase
    implementation(platform("com.google.firebase:firebase-bom:33.1.2"))
    // Añadir la dependencia para Firebase Cloud Messaging
    implementation("com.google.firebase:firebase-messaging")
    implementation("androidx.multidex:multidex:2.0.1")
    // --- FIN ---
}