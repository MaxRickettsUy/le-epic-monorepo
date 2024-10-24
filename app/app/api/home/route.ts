import { Band } from '@/lib/types';
import { faker } from '@faker-js/faker';

const capitalizeFirstLetter = (value: string) => {
  return value.charAt(0).toUpperCase() + value.slice(1);
}

export async function GET(req: Request) {
  const bands: Band[] = [...new Array(10)].map((_, index) => {
    return {
      name: capitalizeFirstLetter(faker.word.noun(100)),
      status: "active",
      members: [
        {
          name: faker.person.fullName(),
          role: "vocals"
        },
        {
          name: faker.person.fullName(),
          role: "guitarist"
        },
        {
          name: faker.person.fullName(),
          role: "drums"
        },
        {
          name: faker.person.fullName(),
          role: "bass"
        }
      ],
      discography: []
    }
  })

  return Response.json(bands);
}