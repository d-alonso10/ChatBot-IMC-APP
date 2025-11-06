// lib/screens/auth_screen.dart
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';

class AuthScreen extends StatefulWidget {
  const AuthScreen({Key? key}) : super(key: key);

  @override
  _AuthScreenState createState() => _AuthScreenState();
}

class _AuthScreenState extends State<AuthScreen> {
  final _formKey = GlobalKey<FormState>();
  var _isLogin = true;
  var _isLoading = false;
  String _email = '';
  String _password = '';

  void _trySubmit() async {
    final isValid = _formKey.currentState?.validate() ?? false;
    FocusScope.of(context).unfocus();

    if (isValid) {
      _formKey.currentState!.save();
      setState(() {
        _isLoading = true;
      });

      try {
        if (_isLogin) {
          await Provider.of<AuthProvider>(context, listen: false)
              .login(_email, _password);
        } else {
          await Provider.of<AuthProvider>(context, listen: false)
              .register(_email, _password);
        }
      } catch (error) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(error.toString().replaceAll("Exception: ", "")),
            backgroundColor: Theme.of(context).colorScheme.error,
          ),
        );
      } finally {
        if (mounted) {
          setState(() {
            _isLoading = false;
          });
        }
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    // Para que el formulario sea más ancho, podemos ajustar el ancho de la tarjeta.
    // Usaremos un porcentaje del ancho de la pantalla.
    final deviceSize = MediaQuery.of(context).size;

    return Scaffold(
      backgroundColor: Theme.of(context).primaryColor,
      body: Center(
        child: SingleChildScrollView(
          child: Card(
            margin: const EdgeInsets.all(20),
            // --- AJUSTES DE ANCHO Y ELEVACIÓN DEL CARD ---
            elevation: 8,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
            child: Container(
              width: deviceSize.width * 0.85, // 85% del ancho de la pantalla
              padding: const EdgeInsets.all(25), // Más padding para que el contenido respire
              // --- FIN AJUSTES CARD ---
              child: Form(
                key: _formKey,
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: <Widget>[
                    Text(
                      _isLogin ? 'Iniciar Sesión' : 'Crear Cuenta',
                      style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                        color: Theme.of(context).primaryColor, // Usar el color primario
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 30), // Espacio un poco mayor
                    TextFormField(
                      key: const ValueKey('email'),
                      validator: (value) {
                        if (value == null || !value.contains('@')) {
                          return 'Por favor ingrese un email válido.';
                        }
                        return null;
                      },
                      keyboardType: TextInputType.emailAddress,
                      decoration: const InputDecoration(
                        labelText: 'Email',
                        border: OutlineInputBorder(), // Estilo de borde
                        prefixIcon: Icon(Icons.email), // Icono
                      ),
                      onSaved: (value) {
                        _email = value ?? '';
                      },
                    ),
                    const SizedBox(height: 20), // Espacio entre campos
                    TextFormField(
                      key: const ValueKey('password'),
                      validator: (value) {
                        if (value == null || value.length < 5) {
                          return 'La contraseña debe tener al menos 5 caracteres.';
                        }
                        return null;
                      },
                      decoration: const InputDecoration(
                        labelText: 'Contraseña',
                        border: OutlineInputBorder(), // Estilo de borde
                        prefixIcon: Icon(Icons.lock), // Icono
                      ),
                      obscureText: true,
                      onSaved: (value) {
                        _password = value ?? '';
                      },
                    ),
                    const SizedBox(height: 30), // Espacio un poco mayor antes del botón
                    if (_isLoading)
                      const CircularProgressIndicator(),
                    if (!_isLoading)
                      // --- ESTILO DE BOTÓN MEJORADO ---
                      SizedBox(
                        width: double.infinity, // Ocupar todo el ancho disponible
                        height: 50, // Altura un poco mayor
                        child: ElevatedButton(
                          style: ElevatedButton.styleFrom(
                            backgroundColor: Theme.of(context).primaryColor, // Color primario
                            foregroundColor: Colors.white, // Texto blanco
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(10), // Bordes redondeados
                            ),
                            elevation: 5, // Sombra para el botón
                          ),
                          onPressed: _trySubmit,
                          child: Text(
                            _isLogin ? 'Login' : 'Registrar',
                            style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                          ),
                        ),
                      ),
                      // --- FIN ESTILO BOTÓN ---
                    const SizedBox(height: 15), // Espacio después del botón
                    if (!_isLoading)
                      TextButton(
                        child: Text(
                          _isLogin ? 'Crear una nueva cuenta' : 'Ya tengo una cuenta',
                          style: TextStyle(color: Theme.of(context).primaryColor),
                        ),
                        onPressed: () {
                          setState(() {
                            _isLogin = !_isLogin;
                          });
                        },
                      )
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}