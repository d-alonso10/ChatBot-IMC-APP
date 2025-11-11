// lib/main.dart
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

// --- AÑADIDOS PARA FIREBASE ---
import 'package:firebase_core/firebase_core.dart';
import 'services/notification_service.dart';
// Importa el archivo que generará 'flutterfire_cli'
// import 'firebase_options.dart'; 
// --- FIN DE AÑADIDOS ---

import 'providers/auth_provider.dart';
import 'providers/paciente_provider.dart';
import 'screens/splash_screen.dart';
import 'screens/auth_screen.dart';
import 'screens/paciente_screen.dart';

// --- ¡FUNCIÓN MAIN MODIFICADA! ---
Future<void> main() async {
  // Asegurarnos que Flutter esté inicializado
  WidgetsFlutterBinding.ensureInitialized();
  
  // Inicializar Firebase
  // ¡¡IMPORTANTE!! Esto fallará hasta que ejecutes `flutterfire configure`
  // y se cree el archivo 'firebase_options.dart'.
  try {
    // await Firebase.initializeApp(
    //   options: DefaultFirebaseOptions.currentPlatform,
    // );
    // --- NOTA: Comentado temporalmente para evitar un crash
    // --- hasta que configures tu proyecto en Firebase.
    // --- Descoméntalo cuando `firebase_options.dart` exista.

  } catch (e) {
    print("Error al inicializar Firebase: $e");
  }

  // Inicializar el manejador de notificaciones en segundo plano
  await NotificationService.init();

  // Ejecutar la app
  runApp(const ChatIMCApp());
}
// --- FIN DE LA MODIFICACIÓN ---

class ChatIMCApp extends StatelessWidget {
  const ChatIMCApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => AuthProvider()),
        ChangeNotifierProxyProvider<AuthProvider, PacienteProvider>(
          create: (ctx) => PacienteProvider(null, []),
          update: (ctx, auth, previousPacientes) => PacienteProvider(
            auth.token,
            previousPacientes == null ? [] : previousPacientes.pacientes,
          ),
        ),
      ],
      child: Consumer<AuthProvider>(
        builder: (ctx, auth, _) => MaterialApp(
          title: 'Chat IMC Pediátrico',
          theme: ThemeData(
            primarySwatch: Colors.deepPurple,
            useMaterial3: true,
          ),
          home: auth.isAuth
              ? const PacienteScreen()
              : FutureBuilder(
                  future: auth.tryAutoLogin(),
                  builder: (ctx, authResultSnapshot) =>
                      authResultSnapshot.connectionState == ConnectionState.waiting
                          ? const SplashScreen()
                          : const AuthScreen(),
                ),
          debugShowCheckedModeBanner: false,
        ),
      ),
    );
  }
}