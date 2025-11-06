// lib/main.dart
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'providers/auth_provider.dart';
import 'providers/paciente_provider.dart';
import 'screens/splash_screen.dart';
import 'screens/auth_screen.dart';
import 'screens/paciente_screen.dart';

void main() => runApp(const ChatIMCApp());

class ChatIMCApp extends StatelessWidget {
  const ChatIMCApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => AuthProvider()),
        // PacienteProvider depende de AuthProvider.
        // Usamos ChangeNotifierProxyProvider para pasarle el token.
        ChangeNotifierProxyProvider<AuthProvider, PacienteProvider>(
          create: (ctx) => PacienteProvider(null, []),
          update: (ctx, auth, previousPacientes) => PacienteProvider(
            auth.token,
            previousPacientes == null ? [] : previousPacientes.pacientes,
          ),
        ),
        // ChatProvider ahora se creará en PacienteScreen,
        // así que ya no es necesario aquí.
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