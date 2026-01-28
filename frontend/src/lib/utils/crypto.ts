/* path: frontend/src/lib/utils/crypto.ts
   version: 1.0
   
   Cryptographic utilities for client-side password hashing
   
   Security model:
   - Passwords are NEVER sent in plaintext
   - SHA256 computed client-side before transmission
   - Backend receives SHA256(password) and stores bcrypt(SHA256(password))
*/

/**
 * Compute SHA256 hash of a string using Web Crypto API
 * 
 * @param message - String to hash (typically a password)
 * @returns Promise resolving to hexadecimal SHA256 hash (64 chars)
 * 
 * @example
 * const hash = await sha256("MyPassword123");
 * // Returns: "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8"
 */
export async function sha256(message: string): Promise<string> {
    const msgBuffer = new TextEncoder().encode(message);
    const hashBuffer = await crypto.subtle.digest('SHA-256', msgBuffer);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    const hashHex = hashArray
      .map(b => b.toString(16).padStart(2, '0'))
      .join('');
    
    return hashHex;
  }
  
  /**
   * Hash a password for secure transmission to backend
   * 
   * @param password - Plaintext password
   * @returns Promise resolving to SHA256 hash
   * 
   * @example
   * const passwordHash = await hashPasswordForTransmission("MyPassword123");
   * await apiClient.post("/auth/login", { email, password_hash: passwordHash });
   */
  export async function hashPasswordForTransmission(password: string): Promise<string> {
    return sha256(password);
  }