declare namespace AppleID {
  interface AuthI {
    init(config: { clientId: string; scope: string; redirectURI: string; usePopup: boolean }): void;
    signIn(): Promise<{
      authorization: {
        code: string;
        id_token: string;
        state?: string;
      };
      user?: {
        email?: string;
        name?: { firstName?: string; lastName?: string };
      };
    }>;
  }
  const auth: AuthI;
}
