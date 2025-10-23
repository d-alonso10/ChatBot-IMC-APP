import 'package:flutter/material.dart';
import 'package:flutter/material.dart';
import 'screens/splash_screen.dart'; // ✅ cambia esta línea

void main() => runApp(ChatIMCApp());

class ChatIMCApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Chat IMC Pediátrico',
      theme: ThemeData(
        primarySwatch: Colors.deepPurple,
      ),
      home: SplashScreen(), // ✅ Pantalla de bienvenida animada
      debugShowCheckedModeBanner: false,
    );
  }
}

