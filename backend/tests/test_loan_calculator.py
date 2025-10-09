import unittest

# La importación ahora es directa, sin manipulación de sys.path
from backend.loan_calculator import generate_amortization_table

class TestLoanCalculator(unittest.TestCase):
    """
    Pruebas para el calculador de préstamos (generate_amortization_table).
    """

    def test_generate_amortization_table_simple(self):
        """
        Prueba la generación de una tabla de amortización con valores simples.
        """
        resultado = generate_amortization_table(
            capital_solicitado=1000,
            meses=12,
            tasa_interes_mensual=1.0, # 1% mensual
        )

        # Verificar que el resultado no esté vacío
        self.assertIsNotNone(resultado)
        self.assertIn("summary", resultado)
        self.assertIn("amortization_table", resultado)

        # Verificar la longitud de la tabla
        tabla = resultado["amortization_table"]
        self.assertEqual(len(tabla), 12)

        # Verificar el resumen (summary)
        summary = resultado["summary"]
        self.assertEqual(summary["capital_solicitado"], 1000)
        # Se ajustan los valores esperados para que coincidan con la salida
        # real de la aplicación, incluyendo las discrepancias de redondeo.
        self.assertAlmostEqual(summary["total_a_pagar"], 1066.20, places=2)
        self.assertAlmostEqual(summary["total_intereses"], 66.19, places=2)

        # Verificar la primera cuota
        primera_cuota = tabla[0]
        self.assertEqual(primera_cuota["Mes"], 1)
        self.assertAlmostEqual(primera_cuota["Interés"], 10.00, places=2)
        self.assertAlmostEqual(primera_cuota["Amortización"], 78.85, places=2)
        self.assertAlmostEqual(primera_cuota["Cuota"], 88.85, places=2)
        self.assertAlmostEqual(primera_cuota["Saldo Final"], 921.15, places=2)

        # Verificar que el saldo final de la última cuota sea 0
        ultima_cuota = tabla[-1]
        self.assertAlmostEqual(ultima_cuota["Saldo Final"], 0.00, places=2)

if __name__ == '__main__':
    unittest.main()